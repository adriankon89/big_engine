from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import router
from app.core.handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.infrastructure.rate_limiter import limiter

setup_logging()
app = FastAPI(title="Bid Engine API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

register_exception_handlers(app)

app.include_router(router)
