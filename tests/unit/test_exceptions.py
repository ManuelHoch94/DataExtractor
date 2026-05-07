import pytest

from data_extractor.core.exceptions import (
    ConfigurationError,
    DataExtractorError,
    ExtractorError,
    ProcessorError,
    ReaderError,
)


def test_hierarchy():
    for exc_class in (ReaderError, ProcessorError, ExtractorError, ConfigurationError):
        assert issubclass(exc_class, DataExtractorError)


def test_raise_reader_error():
    with pytest.raises(ReaderError, match="bad file"):
        raise ReaderError("bad file")


def test_raise_processor_error():
    with pytest.raises(ProcessorError):
        raise ProcessorError("oops")


def test_raise_extractor_error():
    with pytest.raises(ExtractorError):
        raise ExtractorError("oops")


def test_raise_configuration_error():
    with pytest.raises(ConfigurationError):
        raise ConfigurationError("missing key")
