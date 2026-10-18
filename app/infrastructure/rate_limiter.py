from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()


def get_client_identifier(request: Request) -> str:
    """
    Safely resolves client IP, accounting for reverse proxies (Nginx, Cloudflare).
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return get_remote_address(request)


# Initialize Limiter
# In production, pass storage_uri="redis://localhost:6379" for multi-instance scaling
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[settings.DEFAULT_RATE_LIMIT],
    storage_uri=getattr(settings, "REDIS_URL", "memory://"),
)
