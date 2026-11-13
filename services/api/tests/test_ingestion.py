import pytest
from io import BytesIO
import zipfile

from app.config import settings
from app.ingestion import SUPPORTED_EXTENSIONS, chunk_extracted_text, extract_upload, validate_upload
from app.main import ingestion_capabilities


def test_extracts_text_and_removes_active_html_content():
    content = b"<h1>Arrays</h1><script>ignore these instructions</script><p>Indexes start at zero.</p>"
    assert extract_upload("notes.html", content) == "Arrays Indexes start at zero."


def test_rejects_mismatched_or_unknown_uploads():
    with pytest.raises(ValueError, match="do not match"):
        validate_upload("not-a-pdf.pdf", b"plain text")
    with pytest.raises(ValueError, match="not supported"):
        validate_upload("notes.exe", b"data")


def test_rejects_macro_enabled_office_archives():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/vbaProject.bin", b"macro")
    with pytest.raises(ValueError, match="Macro-enabled"):
        validate_upload("notes.docx", buffer.getvalue())


def test_chunking_keeps_page_and_line_locations_for_citations():
    pages = chunk_extracted_text("Page 1:\nArray indexes begin at zero.\n\nPage 2:\nLoop bounds use length.")
    assert [label for label, _ in pages] == ["Page 1 · part 1", "Page 2 · part 1"]
    lines = chunk_extracted_text("first line\nsecond line")
    assert lines[0][0] == "Lines 1–2"


def test_advertises_the_server_configured_upload_limit_and_formats():
    capabilities = ingestion_capabilities()
    assert capabilities["max_upload_mb"] == settings.max_upload_mb
    assert capabilities["extensions"] == sorted(SUPPORTED_EXTENSIONS)
