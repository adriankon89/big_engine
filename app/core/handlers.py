from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError


async def custom_404_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Podany zasób lub punkt końcowy nie istnieje.",
            "path": request.url.path,
        },
    )


async def user_already_exists_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
    )


async def user_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


async def permission_denied_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)}
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(404, custom_404_handler)
    app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(PermissionError, permission_denied_handler)
