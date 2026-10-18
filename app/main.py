from fastapi import FastAPI

from app.api import router
from app.core.handlers import register_exception_handlers
from app.core.logging import setup_logging

setup_logging()
app = FastAPI(title="Bid Engine API", version="0.1.0")
register_exception_handlers(app)

app.include_router(router)
