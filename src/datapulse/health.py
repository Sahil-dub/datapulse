from datapulse.config import settings


def get_health() -> dict[str, str]:
    """Return basic application health information."""
    return {
        "status": "ok",
        "application": settings.app_name,
        "environment": settings.environment,
    }
