from __future__ import annotations

import logging

from data_extractor.config.settings import Settings
from data_extractor.core.models import ExtractionRequest, ExtractionResult
from data_extractor.extractors.field_extractor import FieldExtractor
from data_extractor.llm.base import BaseLLMClient
from data_extractor.processors.index_mapper import IndexMapper
from data_extractor.processors.text_processor import TextProcessor
from data_extractor.readers.base import BaseReader
from data_extractor.readers.pdf_reader import PdfReader
from data_extractor.utils.helpers import resolve_reader

logger = logging.getLogger(__name__)


def _build_llm_client(settings: Settings) -> BaseLLMClient:
    """Instantiate the configured LLM backend from *settings*."""
    if settings.llm_provider == "openai":
        from data_extractor.llm.openai_client import OpenAIClient

        return OpenAIClient(
            api_key=settings.openai_api_key.get_secret_value(),  # type: ignore[union-attr]
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )

    from data_extractor.llm.anthropic_client import AnthropicClient

    return AnthropicClient(
        api_key=settings.anthropic_api_key.get_secret_value(),  # type: ignore[union-attr]
        model=settings.anthropic_model,
    )


class Orchestrator:
    """Top-level component that wires readers, processors and extractors together.

    The active LLM provider is determined at construction time via
    :meth:`from_settings`.  Swap providers by changing ``LLM_PROVIDER``
    in the environment – no code changes required.

    Usage::

        settings = Settings()
        orch = Orchestrator.from_settings(settings)
        result = orch.run(ExtractionRequest(
            file_path=Path("invoice.pdf"),
            schema_definition={"invoice_number": "The unique invoice ID"},
        ))
        print(result.to_index_dict())
    """

    def __init__(
        self,
        readers: list[BaseReader],
        text_processor: TextProcessor,
        field_extractor: FieldExtractor,
    ) -> None:
        self._readers = readers
        self._text_processor = text_processor
        self._field_extractor = field_extractor

    @classmethod
    def from_settings(cls, settings: Settings) -> Orchestrator:
        """Factory – builds a fully-wired :class:`Orchestrator` from *settings*."""
        llm_client = _build_llm_client(settings)
        mapper = IndexMapper(
            llm_client=llm_client,
            max_tokens=settings.extraction_max_tokens,
        )
        extractor = FieldExtractor(
            index_mapper=mapper,
            confidence_threshold=settings.extraction_confidence_threshold,
        )
        return cls(
            readers=[PdfReader()],
            text_processor=TextProcessor(),
            field_extractor=extractor,
        )

    def run(self, request: ExtractionRequest) -> ExtractionResult:
        """Execute the full extraction pipeline for *request*."""
        logger.info("Starting extraction for '%s'", request.file_path)

        reader = resolve_reader(request.file_path, self._readers)
        read_result = reader.read(request.file_path, max_pages=request.max_pages)

        clean_text = self._text_processor.process(read_result.text)

        fields = self._field_extractor.extract(
            text=clean_text,
            schema_definition=request.schema_definition,
        )

        result = ExtractionResult(
            request=request,
            fields=fields,
            raw_text=clean_text,
            page_count=read_result.page_count,
            metadata=read_result.metadata,
        )

        logger.info(
            "Extraction complete: %d fields extracted from %d pages",
            len(fields),
            read_result.page_count,
        )
        return result
