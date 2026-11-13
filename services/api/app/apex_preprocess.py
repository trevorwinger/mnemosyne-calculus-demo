"""Extract compact, citable Calc I study sources from a local APEX Calculus PDF."""
from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


# Printed book pages. The supplied APEX Calculus PDF has twelve front-matter pages.
CALC_I_SECTIONS = (
    ("1.1", "An Introduction To Limits", "Chapter 1 · Limits", 1, 9),
    ("1.3", "Finding Limits Analytically", "Chapter 1 · Limits", 17, 29),
    ("1.4", "One-Sided Limits", "Chapter 1 · Limits", 29, 38),
    ("1.5", "Continuity", "Chapter 1 · Limits", 38, 50),
    ("2.1", "Instantaneous Rates of Change: The Derivative", "Chapter 2 · Derivatives", 62, 78),
    ("2.3", "Basic Differentiation Rules", "Chapter 2 · Derivatives", 85, 92),
    ("2.4", "The Product and Quotient Rules", "Chapter 2 · Derivatives", 92, 102),
    ("2.5", "The Chain Rule", "Chapter 2 · Derivatives", 102, 111),
    ("2.6", "Implicit Differentiation", "Chapter 2 · Derivatives", 111, 122),
    ("3.1", "Extreme Values", "Chapter 3 · Using Derivatives", 128, 136),
    ("3.2", "The Mean Value Theorem", "Chapter 3 · Using Derivatives", 136, 142),
    ("3.3", "Increasing and Decreasing Functions", "Chapter 3 · Using Derivatives", 142, 150),
    ("3.4", "Concavity and the Second Derivative", "Chapter 3 · Using Derivatives", 150, 159),
    ("4.2", "Related Rates", "Chapter 4 · Derivative Applications", 173, 182),
    ("4.3", "Optimization", "Chapter 4 · Derivative Applications", 182, 189),
)
ATTRIBUTION = "Source: APEX Calculus, 5th edition (2026), Gregory Hartman et al., CC BY-NC 4.0. https://www.apexcalculus.com"


def section_excerpt(section: str, title: str, text: str) -> str:
    """Keep an overview and several worked examples without importing an entire chapter."""
    text = re.sub(r"\n{3,}", "\n\n", text.replace("\x00", "")).strip()
    # Text extraction often collapses typography, yielding `Example2.4.3`.
    example_starts = list(re.finditer(r"(?=\bExample\s*" + re.escape(section) + r"\.\d+)", text, flags=re.IGNORECASE))
    overview_end = example_starts[0].start() if example_starts else min(len(text), 2200)
    overview = text[:overview_end].strip()[:2200]
    excerpts = [f"{ATTRIBUTION}\n\nSection {section}: {title}\n\nSection introduction:\n{overview}"]
    for index, start in enumerate(example_starts[:3], start=1):
        end = example_starts[index].start() if index < len(example_starts) else len(text)
        example = text[start.start():end].strip()[:2600]
        if example:
            excerpts.append(f"Worked example {index}:\n{example}")
    return "\n\n".join(excerpts)


def extract_calc_i_sources(pdf_path: str | Path) -> list[dict[str, str]]:
    """Return student-ready section records, or fail clearly for an unusable textbook."""
    source = Path(pdf_path)
    if not source.is_file():
        return []
    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError("The APEX textbook PDF is encrypted. Provide an unlocked copy in .local-content.")
    records = []
    for section, title, module, first_page, next_page in CALC_I_SECTIONS:
        # PdfReader uses zero-based indexing; printed page 1 is PDF page 13.
        pages = reader.pages[first_page + 11:next_page + 11]
        text = "\n\n".join(page.extract_text() or "" for page in pages)
        if text.strip():
            records.append({"title": f"APEX Calculus §{section} — {title}", "module": module, "text": section_excerpt(section, title, text)})
    if not records:
        raise ValueError("No extractable text was found in the APEX textbook PDF.")
    return records
