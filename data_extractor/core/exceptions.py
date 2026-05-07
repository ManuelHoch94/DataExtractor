class DataExtractorError(Exception):
    """Base exception for all DataExtractor errors."""


class ReaderError(DataExtractorError):
    """Raised when a document reader fails to read or parse a file."""


class ProcessorError(DataExtractorError):
    """Raised when a processor fails during text processing."""


class ExtractorError(DataExtractorError):
    """Raised when a field extractor encounters an error."""


class ConfigurationError(DataExtractorError):
    """Raised when the application configuration is invalid."""
