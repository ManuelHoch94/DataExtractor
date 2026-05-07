import pytest

from data_extractor.processors.text_processor import TextProcessor


@pytest.fixture()
def processor() -> TextProcessor:
    return TextProcessor()


def test_strips_leading_trailing_whitespace(processor: TextProcessor):
    assert processor.process("  hello  ") == "hello"


def test_collapses_multiple_spaces(processor: TextProcessor):
    assert processor.process("foo   bar") == "foo bar"


def test_collapses_multiple_newlines(processor: TextProcessor):
    result = processor.process("a\n\n\n\n\nb")
    assert result == "a\n\nb"


def test_replaces_ligatures(processor: TextProcessor):
    assert processor.process("ﬁle ﬀect") == "file ffect"


def test_removes_soft_hyphen(processor: TextProcessor):
    assert processor.process("connec­tion") == "connection"


def test_empty_string(processor: TextProcessor):
    assert processor.process("") == ""


def test_only_whitespace(processor: TextProcessor):
    assert processor.process("   \n\n   ") == ""


def test_preserves_content(processor: TextProcessor):
    text = "Invoice Number: INV-2024-001\nAmount: 1.500,00 EUR"
    result = processor.process(text)
    assert "INV-2024-001" in result
    assert "1.500,00 EUR" in result


def test_strips_lines(processor: TextProcessor):
    result = processor.process("  line one  \n  line two  ")
    assert result == "line one\nline two"
