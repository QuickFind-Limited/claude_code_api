"""Minimal Claude SDK Server."""

# Only import app when explicitly needed to avoid environment variable issues
def get_app():
    """Get the FastAPI app instance."""
    from .main import app
    return app

__version__ = "1.0.0"
__all__ = ["get_app"]
