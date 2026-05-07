from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from data_extractor.api.dependencies import SchemaStoreDep
from data_extractor.registry.models import SchemaEntry

router = APIRouter(prefix="/schemas", tags=["Schemas"])


class SchemaCreateRequest(SchemaEntry):
    """Request body for creating/updating a schema.

    Inherits all fields from :class:`SchemaEntry`; ``created_at`` and
    ``updated_at`` are set server-side and ignored if provided.
    """


@router.post(
    "",
    response_model=SchemaEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a named extraction schema",
    description=(
        "Save a schema under a unique **name**. If a schema with that name "
        "already exists it is overwritten and `updated_at` is refreshed."
    ),
)
def create_schema(body: SchemaCreateRequest, store: SchemaStoreDep) -> SchemaEntry:
    return store.save(SchemaEntry(**body.model_dump()))


@router.get(
    "",
    response_model=list[SchemaEntry],
    summary="List all stored schemas",
)
def list_schemas(store: SchemaStoreDep) -> list[SchemaEntry]:
    return store.list_all()


@router.get(
    "/{name}",
    response_model=SchemaEntry,
    summary="Get a schema by name",
    responses={404: {"description": "Schema not found"}},
)
def get_schema(name: str, store: SchemaStoreDep) -> SchemaEntry:
    entry = store.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema '{name}' not found.",
        )
    return entry


@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a schema by name",
    responses={404: {"description": "Schema not found"}},
)
def delete_schema(name: str, store: SchemaStoreDep) -> None:
    if not store.delete(name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema '{name}' not found.",
        )
