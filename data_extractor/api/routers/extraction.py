from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from data_extractor.api.dependencies import OrchestratorDep
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
        "Upload a PDF file and a JSON schema definition. "
        "The service extracts the requested fields using AI and returns them "
        "as structured data ready for index ingestion."
    ),
    responses={
        400: {"description": "Invalid file type or malformed request"},
        422: {"description": "Validation error in request parameters"},
        500: {"description": "Internal extraction error"},
    },
)
async def extract(
    orchestrator: OrchestratorDep,
    file: UploadFile = File(..., description="PDF file to extract data from."),
    request: str = Form(
        default="{}",
        description=(
            "JSON-encoded ExtractionRequestSchema. "
            'Example: {"schema_definition": {"invoice_number": "The invoice ID"}}'
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

    content = await file.read()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        extraction_request = ExtractionRequest(
            file_path=tmp_path,
            schema_definition=req_schema.schema_definition,
            max_pages=req_schema.max_pages,
        )

        if req_schema.confidence_threshold is not None:
            orchestrator._field_extractor._confidence_threshold = (
                req_schema.confidence_threshold
            )

        result = orchestrator.run(extraction_request)
    except ReaderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DataExtractorError as exc:
        logger.exception("Extraction failed for file '%s'", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
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


def _validate_upload(file: UploadFile) -> None:
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Only PDF files are accepted."
            ),
        )
    if file.size is not None and file.size > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {_MAX_FILE_SIZE // (1024*1024)} MB.",
        )
