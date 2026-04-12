from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ApiException(HTTPException):
    def __init__(
        self,
        code: str,
        status_code: int = 400,
        detail: dict | None = None,
    ):
        super().__init__(status_code=status_code)
        self.code = code
        self.detail = detail or {}


async def api_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "detail": exc.detail,
            "status": exc.status_code,
        },
    )


async def validation_exception_handler(request: Request, exc):
    def map_fastapi_errors(details: list[dict]) -> dict[str, str]:
        errors: dict[str, str] = {}

        for err in details:
            path = [p for p in err.get("loc", []) if p != "body"]
            field = ".".join(str(p) for p in path)

            errors[field] = err.get("msg", "")

        return errors

    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "detail": map_fastapi_errors(exc.errors()),
            "status": 422,
        },
    )


async def http_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "HTTP_ERROR",
            "detail": exc.detail,
            "status": exc.status_code,
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "detail": {},
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )
