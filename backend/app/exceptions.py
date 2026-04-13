from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Single error detail."""

    kind: str | None = None
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        ErrorDetail(
            kind=".".join(str(loc) for loc in err["loc"][1:]) or None,
            message=err["msg"],
        )
        for err in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle all HTTPExceptions with standard format."""
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        500: "INTERNAL_SERVER_ERROR",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=code_map.get(exc.status_code, "HTTP_ERROR"), message=exc.detail
        ).model_dump(),
    )
