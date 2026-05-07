from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from data_extractor.api.dependencies import OrchestratorDep, SchemaStoreDep
from data_extractor.api.schemas.requests import ExtractionRequestSchema
from data_extractor.api.schemas.responses import ExtractionFieldSchema, ExtractionResponse
from data_extractor.core.exceptions import DataExtractorError, ReaderError
from data_extractor.core.models import ExtractionRequest

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
        "Upload a PDF and specify **which fields to extract** in one of two ways:\n\n"
        "**Option 1 – inline schema** (no setup needed):\n"
        "```json\n"
        '{"schema_definition": {"invoice_number": "The unique invoice ID"}}\n'
        "```\n\n"
        "**Option 2 – saved schema** (create one first via `POST /api/v1/schemas`):\n"
        "```json\n"
        '{"schema_name": "invoice"}\n'
        "```\n\n"
        "When both are provided `schema_definition` takes precedence."
    ),
    responses={
        400: {"description": "Invalid file type, unknown schema name, or malformed request"},
        422: {"description": "Validation error in request parameters"},
        500: {"description": "Internal extraction error"},
    },
)
async def extract(
    orchestrator: OrchestratorDep,
    store: SchemaStoreDep,
    file: UploadFile = File(..., description="PDF file to extract data from."),
    request: str = Form(
        default="{}",
        description=(
            "JSON-encoded ExtractionRequestSchema. "
            'Example: {"schema_name": "invoice"} or '
            '{"schema_definition": {"invoice_number": "The invoice ID"}}'
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

    schema_definition = _resolve_schema(req_schema, store)

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
        logger.exception("Extraction failed for file '%s'", file.filename)
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


def _resolve_schema(
    req: ExtractionRequestSchema,
    store,
) -> dict[str, str]:
    """Return the effective schema_definition for the request.

    Precedence: inline schema_definition > schema_name lookup > empty dict.
    """
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
