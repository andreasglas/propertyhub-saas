from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class PropertyHubError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PropertyHubError)
    async def handle_propertyhub_error(
        _: Request, exc: PropertyHubError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
