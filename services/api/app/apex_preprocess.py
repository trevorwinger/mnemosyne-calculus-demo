"""Extract compact, citable Calc III study sources from a local APEX Calculus PDF."""
from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


# Printed book pages. The supplied APEX Calculus PDF has twelve front-matter pages.
CALC_III_SECTIONS = (
    ("9.1", "Sequences", "Chapter 9 · Sequences and Series", 442, 457),
    ("9.2", "Infinite Series", "Chapter 9 · Sequences and Series", 457, 473),
    ("9.3", "Integral and Comparison Tests", "Chapter 9 · Sequences and Series", 473, 483),
    ("9.4", "Ratio and Root Tests", "Chapter 9 · Sequences and Series", 483, 490),
    ("9.5", "Alternating Series and Absolute Convergence", "Chapter 9 · Sequences and Series", 490, 500),
    ("9.6", "Power Series", "Chapter 9 · Sequences and Series", 500, 511),
    ("9.7", "Taylor Polynomials", "Chapter 9 · Sequences and Series", 511, 522),
    ("9.8", "Taylor Series", "Chapter 9 · Sequences and Series", 522, 535),
    ("10.1", "Conic Sections", "Chapter 10 · Curves in the Plane", 535, 549),
    ("10.2", "Parametric Equations", "Chapter 10 · Curves in the Plane", 549, 559),
    ("10.3", "Calculus and Parametric Equations", "Chapter 10 · Curves in the Plane", 559, 569),
    ("10.4", "Introduction to Polar Coordinates", "Chapter 10 · Curves in the Plane", 569, 583),
    ("10.5", "Calculus and Polar Functions", "Chapter 10 · Curves in the Plane", 583, 594),
    ("11.1", "Introduction to Cartesian Coordinates in Space", "Chapter 11 · Vectors", 594, 610),
    ("11.2", "An Introduction to Vectors", "Chapter 11 · Vectors", 610, 623),
    ("11.3", "The Dot Product", "Chapter 11 · Vectors", 623, 636),
    ("11.4", "The Cross Product", "Chapter 11 · Vectors", 636, 646),
    ("11.5", "Lines", "Chapter 11 · Vectors", 646, 655),
    ("11.6", "Planes", "Chapter 11 · Vectors", 655, 662),
    ("12.1", "Vector-Valued Functions", "Chapter 12 · Vector-Valued Functions", 662, 669),
    ("12.2", "Calculus and Vector-Valued Functions", "Chapter 12 · Vector-Valued Functions", 669, 681),
    ("12.3", "The Calculus of Motion", "Chapter 12 · Vector-Valued Functions", 681, 694),
    ("12.4", "Unit Tangent and Normal Vectors", "Chapter 12 · Vector-Valued Functions", 694, 703),
    ("12.5", "The Arc Length Parameter and Curvature", "Chapter 12 · Vector-Valued Functions", 703, 714),
    ("13.1", "Introduction to Multivariable Functions", "Chapter 13 · Functions of Several Variables", 714, 722),
    ("13.2", "Limits and Continuity of Multivariable Functions", "Chapter 13 · Functions of Several Variables", 722, 731),
    ("13.3", "Partial Derivatives", "Chapter 13 · Functions of Several Variables", 731, 743),
    ("13.4", "Differentiability and the Total Differential", "Chapter 13 · Functions of Several Variables", 743, 752),
    ("13.5", "The Multivariable Chain Rule", "Chapter 13 · Functions of Several Variables", 752, 761),
    ("13.6", "Directional Derivatives", "Chapter 13 · Functions of Several Variables", 761, 771),
    ("13.7", "Tangent Lines, Normal Lines, and Tangent Planes", "Chapter 13 · Functions of Several Variables", 771, 781),
    ("13.8", "Extreme Values", "Chapter 13 · Functions of Several Variables", 781, 790),
    ("14.1", "Iterated Integrals and Area", "Chapter 14 · Multiple Integration", 790, 799),
    ("14.2", "Double Integration and Volume", "Chapter 14 · Multiple Integration", 799, 810),
    ("14.3", "Double Integration with Polar Coordinates", "Chapter 14 · Multiple Integration", 810, 819),
    ("14.4", "Center of Mass", "Chapter 14 · Multiple Integration", 819, 831),
    ("14.5", "Surface Area", "Chapter 14 · Multiple Integration", 831, 838),
    ("14.6", "Volume Between Surfaces and Triple Integration", "Chapter 14 · Multiple Integration", 838, 860),
    ("14.7", "Triple Integration with Cylindrical and Spherical Coordinates", "Chapter 14 · Multiple Integration", 860, 872),
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


def extract_calc_iii_sources(pdf_path: str | Path) -> list[dict[str, str]]:
    """Return student-ready section records, or fail clearly for an unusable textbook."""
    source = Path(pdf_path)
    if not source.is_file():
        return []
    reader = PdfReader(str(source))
    if reader.is_encrypted:
        raise ValueError("The APEX textbook PDF is encrypted. Provide an unlocked copy in .local-content.")
    records = []
    for section, title, module, first_page, next_page in CALC_III_SECTIONS:
        # PdfReader uses zero-based indexing; printed page 1 is PDF page 13.
        pages = reader.pages[first_page + 11:next_page + 11]
        text = "\n\n".join(page.extract_text() or "" for page in pages)
        if text.strip():
            records.append({"title": f"APEX Calculus §{section} — {title}", "module": module, "text": section_excerpt(section, title, text)})
    if not records:
        raise ValueError("No extractable text was found in the APEX textbook PDF.")
    return records
