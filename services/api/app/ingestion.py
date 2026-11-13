"""Local, private material ingestion helpers used by the API and worker."""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
import tempfile
import zipfile
from html.parser import HTMLParser
from io import BytesIO, StringIO
from pathlib import Path

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "txt", "md", "csv", "html", "htm", "rtf", "odt", "odp", "png", "jpg", "jpeg"}
LEGACY_OFFICE_EXTENSIONS = {"doc", "ppt", "xls", "odt", "odp", "rtf"}
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 5000
STRUCTURE_MARKER = re.compile(r"^(Page \d+(?: \(OCR\))?|Slide \d+|Sheet [^:\n]+|Heading [^:\n]+):\s*$", re.MULTILINE)


class _TextOnlyHtml(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts: list[str] = []; self.ignored_depth = 0
    def handle_starttag(self, tag: str, attrs):
        if tag.lower() in {"script", "style", "noscript", "iframe", "object"}: self.ignored_depth += 1
    def handle_endtag(self, tag: str):
        if tag.lower() in {"script", "style", "noscript", "iframe", "object"} and self.ignored_depth: self.ignored_depth -= 1
    def handle_data(self, data: str):
        if not self.ignored_depth: self.parts.append(data)


def extension_for(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_upload(filename: str, data: bytes) -> str:
    suffix = extension_for(filename)
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f".{suffix or 'unknown'} is not supported. Use PDF, Word, PowerPoint, Excel, text, HTML, OpenDocument, or an image file.")
    signatures = {
        "pdf": data.startswith(b"%PDF"),
        "png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "jpg": data.startswith(b"\xff\xd8\xff"),
        "jpeg": data.startswith(b"\xff\xd8\xff"),
    }
    if suffix in signatures and not signatures[suffix]: raise ValueError(f"The file contents do not match the .{suffix} extension.")
    if suffix in {"docx", "pptx", "xlsx", "odt", "odp"} and not data.startswith(b"PK\x03\x04"):
        raise ValueError(f"The file contents do not match the .{suffix} extension.")
    if suffix in {"doc", "ppt", "xls"} and not data.startswith(b"\xd0\xcf\x11\xe0"):
        raise ValueError(f"The file contents do not match the .{suffix} extension.")
    if suffix in {"docx", "pptx", "xlsx", "odt", "odp"}:
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                files = archive.infolist()
                if len(files) > MAX_ARCHIVE_ENTRIES: raise ValueError("This document contains too many embedded files to process safely.")
                if sum(item.file_size for item in files) > MAX_ARCHIVE_UNCOMPRESSED_BYTES: raise ValueError("This document expands beyond the 100 MB safety limit.")
                if any(item.filename.lower().endswith(("vbaproject.bin", "vbadata.xml")) for item in files): raise ValueError("Macro-enabled Office documents are not accepted. Remove macros and export a clean copy.")
        except zipfile.BadZipFile as error:
            raise ValueError(f"The file contents do not match the .{suffix} extension.") from error
    return suffix


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted: raise ValueError("Encrypted PDFs cannot be processed. Upload an unlocked copy.")
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(f"Page {index + 1}:\n{content}" for index, content in enumerate(pages))
    if any(page.strip() for page in pages): return text
    return _ocr_pdf(data, len(pages))


def _ocr_pdf(data: bytes, page_count: int) -> str:
    if page_count > 20: raise ValueError("This scanned PDF has more than 20 pages. Split it before uploading for OCR.")
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError as error: raise ValueError("OCR support is not installed in this environment.") from error
    images = convert_from_bytes(data, dpi=180, fmt="png", thread_count=1)
    return "\n\n".join(f"Page {index + 1} (OCR):\n{pytesseract.image_to_string(image)}" for index, image in enumerate(images))


def _ocr_image(data: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract
    except ImportError as error: raise ValueError("OCR support is not installed in this environment.") from error
    return "Image (OCR):\n" + pytesseract.image_to_string(Image.open(BytesIO(data)))


def _legacy_to_pdf(filename: str, data: bytes) -> bytes:
    if not shutil.which("libreoffice"): raise ValueError("Legacy Office conversion is unavailable. Install LibreOffice in the worker image.")
    suffix = extension_for(filename)
    with tempfile.TemporaryDirectory(prefix="office-hours-ingest-") as tmp:
        source = Path(tmp) / f"source.{suffix}"; source.write_bytes(data)
        result = subprocess.run(["libreoffice", "--headless", "--nologo", "--nodefault", "--nolockcheck", "--norestore", "--convert-to", "pdf", "--outdir", tmp, str(source)], capture_output=True, text=True, timeout=90, check=False)
        converted = Path(tmp) / "source.pdf"
        if result.returncode != 0 or not converted.exists(): raise ValueError("The office document could not be converted. Export it as a current PDF or Office format and try again.")
        return converted.read_bytes()


def extract_upload(filename: str, data: bytes) -> str:
    suffix = validate_upload(filename, data)
    if suffix in {"txt", "md"}: return data.decode("utf-8", errors="replace")
    if suffix == "csv": return "\n".join(f"Row {index}: " + " | ".join(row) for index, row in enumerate(csv.reader(StringIO(data.decode("utf-8", errors="replace"))), start=1))
    if suffix in {"html", "htm"}:
        parser = _TextOnlyHtml(); parser.feed(data.decode("utf-8", errors="replace")); return " ".join(parser.parts)
    if suffix == "pdf": return _pdf_text(data)
    if suffix == "docx":
        from docx import Document
        document = Document(BytesIO(data)); parts = []
        for index, item in enumerate(document.paragraphs, start=1):
            text = item.text.strip()
            if not text: continue
            style = (item.style.name or "").lower()
            parts.append(f"Heading {text}:" if style.startswith("heading") else f"Paragraph {index}: {text}")
        return "\n".join(parts)
    if suffix == "pptx":
        from pptx import Presentation
        presentation = Presentation(BytesIO(data)); pages = []
        for index, slide in enumerate(presentation.slides):
            body = "\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text"))
            notes = "\n".join(shape.text for shape in slide.notes_slide.shapes if hasattr(shape, "text")) if slide.has_notes_slide else ""
            pages.append(f"Slide {index + 1}:\n{body}\n{notes}".strip())
        return "\n\n".join(pages)
    if suffix == "xlsx":
        from openpyxl import load_workbook
        book = load_workbook(BytesIO(data), read_only=True, data_only=True)
        return "\n\n".join(f"Sheet {sheet.title}:\n" + "\n".join(" | ".join(str(cell) if cell is not None else "" for cell in row) for row in sheet.iter_rows(values_only=True)) for sheet in book.worksheets)
    if suffix in {"png", "jpg", "jpeg"}: return _ocr_image(data)
    return _pdf_text(_legacy_to_pdf(filename, data))


def safe_storage_path(upload_dir: str, storage_key: str) -> Path:
    base = Path(upload_dir).resolve(); path = (base / storage_key).resolve()
    if base not in path.parents: raise ValueError("Invalid private upload path.")
    return path


def chunk_extracted_text(text: str, max_chars: int = 1200) -> list[tuple[str, str]]:
    """Split source text while retaining the most useful stable extraction location."""
    text = text.strip()
    if not text: return []
    markers = list(STRUCTURE_MARKER.finditer(text))
    sections: list[tuple[str, str]] = []
    if markers:
        if markers[0].start() > 0: sections.append(("Text", text[:markers[0].start()].strip()))
        for index, marker in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
            sections.append((marker.group(1), text[marker.end():end].strip()))
    else:
        sections = [("Lines", text)]
    chunks: list[tuple[str, str]] = []
    for section_label, section_text in sections:
        if not section_text: continue
        lines = section_text.splitlines(keepends=True)
        current, start_line = "", 1
        for line_number, line in enumerate(lines, start=1):
            if current and len(current) + len(line) > max_chars:
                suffix = f" · part {len([item for item in chunks if item[0].startswith(section_label)]) + 1}"
                label = f"{section_label}{suffix}" if section_label != "Lines" else f"Lines {start_line}–{line_number - 1}"
                chunks.append((label, current.strip())); current, start_line = "", line_number
            current += line
        if current.strip():
            suffix = f" · part {len([item for item in chunks if item[0].startswith(section_label)]) + 1}"
            label = f"{section_label}{suffix}" if section_label != "Lines" else f"Lines {start_line}–{len(lines)}"
            chunks.append((label, current.strip()))
    return chunks
