"""Main entry point for YouTube Music Service."""
import uvicorn
from app.main import app
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        log_level="info"
    )
