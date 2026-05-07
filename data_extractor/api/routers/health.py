from fastapi import APIRouter

from data_extractor.api.dependencies import SettingsDep
from data_extractor.api.schemas.responses import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the application status, version, and active LLM provider.",
)
def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(llm_provider=settings.llm_provider)
