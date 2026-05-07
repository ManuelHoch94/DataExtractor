from unittest.mock import MagicMock

from data_extractor.extractors.field_extractor import FieldExtractor
from data_extractor.processors.index_mapper import IndexMapper


def _make_extractor(mapper: IndexMapper, threshold: float = 0.0) -> FieldExtractor:
    return FieldExtractor(index_mapper=mapper, confidence_threshold=threshold)


def test_extract_delegates_to_mapper(sample_fields):
    mapper = MagicMock(spec=IndexMapper)
    mapper.map.return_value = sample_fields
    extractor = _make_extractor(mapper)

    result = extractor.extract("some text", {"invoice_number": "desc"})

    mapper.map.assert_called_once_with(
        text="some text",
        schema_definition={"invoice_number": "desc"},
        confidence_threshold=0.0,
    )
    assert result == sample_fields


def test_extract_passes_threshold_to_mapper():
    mapper = MagicMock(spec=IndexMapper)
    mapper.map.return_value = []
    extractor = _make_extractor(mapper, threshold=0.7)

    extractor.extract("text", {"field": "desc"})

    _, kwargs = mapper.map.call_args
    assert kwargs["confidence_threshold"] == 0.7


def test_extract_returns_empty_list_when_mapper_empty():
    mapper = MagicMock(spec=IndexMapper)
    mapper.map.return_value = []
    assert _make_extractor(mapper).extract("text", {}) == []
