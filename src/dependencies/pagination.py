from fastapi import (
    status,
    HTTPException,
    Depends,
)
from pydantic import BaseModel


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 10


def pagination_params(skip: int = 0, limit: int = 10) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)


def validated_pagination(
    pagination: PaginationParams = Depends(pagination_params),
) -> PaginationParams:
    if pagination.limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Limit cannot exceed 100"
        )
    return pagination
