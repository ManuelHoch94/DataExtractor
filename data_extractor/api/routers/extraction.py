from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from data_extractor.api.dependencies import OrchestratorDep, SchemaStoreDep
from data_extractor.api.schemas.requests import ExtractionRequestSchema
from data_extractor.api.schemas.responses import ExtractionFieldSchema, ExtractionResponse
from data_extractor.core.exceptions import ConfigurationError, DataExtractorError, ReaderError
from data_extractor.core.models import ExtractionRequest
from data_extractor.registry.schema_file import parse_schema_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extract", tags=["Extraction"])

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post(
    "",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured fields from a PDF",
    description=(
        "Upload a **PDF document** and specify which fields to extract.\n\n"
        "## Schema – three ways (priority order)\n\n"
        "**1. schema_file upload** *(recommended for frontend use)*  \n"
        "Upload a `.json` file alongside the PDF:\n"
        "```json\n"
        '{"invoice_number": "The unique invoice ID", "amount": "Total amount due"}\n'
        "```\n"
        "Also accepts the full format with `name`/`description`/`fields`.\n\n"
        "**2. inline schema_definition** *(API / scripting)*  \n"
        "Pass JSON in the `request` form field:\n"
        '`{"schema_definition": {"invoice_number": "The invoice ID"}}`\n\n'
        "**3. saved schema_name** *(registry lookup)*  \n"
        '`{"schema_name": "invoice"}` — schema must exist in the registry.\n\n'
        "When multiple options are provided, `schema_file` > `schema_definition` > `schema_name`."
    ),
    responses={
        400: {"description": "Invalid file, unknown schema name, or malformed schema JSON"},
        422: {"description": "Validation error in request parameters"},
        500: {"description": "Internal extraction error"},
    },
)
async def extract(
    orchestrator: OrchestratorDep,
    store: SchemaStoreDep,
    file: UploadFile = File(..., description="PDF document to extract data from."),
    schema_file: UploadFile | None = File(
        default=None,
        description=(
            "Optional JSON schema definition file. "
            'Simple format: {"field_name": "description"} or '
            'full format: {"fields": {"field_name": "description"}}.'
        ),
    ),
    request: str = Form(
        default="{}",
        description=(
            "Optional JSON string with extra options: "
            "schema_definition, schema_name, max_pages, confidence_threshold."
        ),
    ),
) -> ExtractionResponse:
    _validate_upload(file)

    try:
        req_schema = ExtractionRequestSchema.model_validate_json(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request JSON: {exc}",
        ) from exc

    schema_definition = await _resolve_schema(req_schema, schema_file, store)

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        extraction_request = ExtractionRequest(
            file_path=tmp_path,
            schema_definition=schema_definition,
            max_pages=req_schema.max_pages,
        )

        if req_schema.confidence_threshold is not None:
            orchestrator._field_extractor._confidence_threshold = (
                req_schema.confidence_threshold
            )

        result = orchestrator.run(extraction_request)
    except ReaderError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DataExtractorError as exc:
        logger.exception("Extraction failed for '%s'", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return ExtractionResponse(
        filename=file.filename or "unknown.pdf",
        page_count=result.page_count,
        fields=[ExtractionFieldSchema(**f.model_dump()) for f in result.fields],
        index=result.to_index_dict(),
        metadata=result.metadata,
    )


async def _resolve_schema(
    req: ExtractionRequestSchema,
    schema_file: UploadFile | None,
    store,
) -> dict[str, str]:
    """Return the effective schema with priority: file > inline > name > empty."""
    if schema_file is not None:
        raw = await schema_file.read()
        try:
            return parse_schema_file(raw)
        except ConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    if req.schema_definition:
        return req.schema_definition

    if req.schema_name:
        entry = store.get(req.schema_name)
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schema '{req.schema_name}' not found in registry.",
            )
        return entry.fields

    return {}


def _validate_upload(file: UploadFile) -> None:
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                "Only PDF files are accepted."
            ),
        )
    if file.size is not None and file.size > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {_MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )
