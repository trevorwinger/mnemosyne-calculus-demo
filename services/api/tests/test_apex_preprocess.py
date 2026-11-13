from app.apex_preprocess import section_excerpt


def test_apex_section_excerpt_removes_pdf_null_characters_and_keeps_three_examples():
    text = "Introduction\x00 to limits.\n\nExample 1.1.1 First.\nSolution.\n\nExample 1.1.2 Second.\nSolution.\n\nExample 1.1.3 Third.\nSolution."
    excerpt = section_excerpt("1.1", "An Introduction To Limits", text)
    assert "\x00" not in excerpt
    assert "Introduction to limits" in excerpt
    assert "Worked example 3" in excerpt


def test_apex_section_excerpt_accepts_pdf_labels_without_a_space_after_example():
    excerpt = section_excerpt("2.4", "The Product Rule", "Example2.4.3 Use the product rule.\nSolution.")
    assert "Worked example 1" in excerpt
