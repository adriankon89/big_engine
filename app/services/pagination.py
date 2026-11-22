from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.schemas.pagination import PaginatedResponse, PaginationParams

ModelT = TypeVar("ModelT")
SchemaT = TypeVar("SchemaT", bound=BaseModel)


def paginate(
    db: Session,
    stmt: Select[tuple[ModelT]],
    params: PaginationParams,
    response_schema: type[SchemaT],
) -> PaginatedResponse[SchemaT]:
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0

    page_stmt = stmt.offset(params.offset).limit(params.page_size)
    rows = db.scalars(page_stmt).all()
    items = [response_schema.model_validate(row) for row in rows]

    return PaginatedResponse[SchemaT].create(
        items=items,
        total=total,
        params=params,
    )
