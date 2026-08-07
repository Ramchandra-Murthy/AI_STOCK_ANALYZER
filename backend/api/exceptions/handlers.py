from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.exceptions import ValidationError, RepositoryError, ValuationError, ServiceError

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": "ValidationError", "detail": str(exc)})

    @app.exception_handler(ValuationError)
    async def valuation_exception_handler(request: Request, exc: ValuationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": "ValuationError", "detail": str(exc)})

    @app.exception_handler(RepositoryError)
    async def repository_exception_handler(request: Request, exc: RepositoryError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": "RepositoryError", "detail": str(exc)})

    @app.exception_handler(ServiceError)
    async def service_exception_handler(request: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": "ServiceError", "detail": str(exc)})