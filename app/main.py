"""Main FastAPI application."""
# Standard library
import time
from contextlib import asynccontextmanager

# Third-party
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Local imports
from app.core.config import get_settings
from app.core.logging_config import setup_logging, get_logger
from app.core.exceptions import YTMusicServiceException
from app.core.exception_handlers import (
    ytmusic_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.api.v1.router import api_router

# Setup logging first
setup_logging()
logger = get_logger(__name__)

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri="memory://"
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {settings.RATE_LIMIT_PER_MINUTE} requests per minute.",
            "retry_after": int(exc.retry_after) if exc.retry_after else 60
        },
        headers={"Retry-After": str(int(exc.retry_after) if exc.retry_after else 60)}
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"API available at http://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}")
    logger.info(f"Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"Caching: {'Enabled' if settings.CACHE_ENABLED else 'Disabled'}")
    logger.info(f"Compression: {'Enabled' if settings.ENABLE_COMPRESSION else 'Disabled'}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    🎵 **YouTube Music API Service** - Servicio completo de API para YouTube Music.
    
    ## Características
    
    - ✅ **Exploración**: Charts, moods, géneros, playlists públicas
    - 🔍 **Búsqueda**: Canciones, videos, álbumes, artistas, playlists
    - 🎧 **Streaming**: URLs directas de audio (best quality)
    - 📱 **Navegación**: Artistas, álbumes, canciones, letras
    - 🎙️ **Podcasts**: Canales, episodios y playlists
    - ⚡ **Rendimiento**: Caché inteligente, circuit breaker, rate limiting
    
    ## Optimizaciones
    
    - **Caché inteligente**: Metadatos (1 día), Stream URLs (4 horas)
    - **Circuit breaker**: Protección contra rate limiting de YouTube
    - **Rate limiting**: 60 requests/minuto por IP
    - **Compresión**: GZip para reducir ancho de banda
    
    ## Manejo de Errores
    
    La API utiliza códigos de error consistentes:
    - `VALIDATION_ERROR` (400): Error de validación en parámetros
    - `AUTHENTICATION_ERROR` (401): Error de autenticación con YouTube
    - `NOT_FOUND` (404): Recurso no encontrado
    - `RATE_LIMIT_ERROR` (429): Límite de peticiones excedido
    - `EXTERNAL_SERVICE_ERROR` (502): Error de servicio externo
    - `SERVICE_UNAVAILABLE` (503): Servicio temporalmente no disponible
    - `INTERNAL_ERROR` (500): Error interno del servidor
    
    ## Documentación
    
    - **Swagger UI**: `/docs` - Interfaz interactiva
    - **ReDoc**: `/redoc` - Documentación alternativa
    """,
    lifespan=lifespan,
    contact={
        "name": "YouTube Music API Service",
        "url": "https://github.com/your-repo",
    },
    license_info={
        "name": "MIT",
    },
    terms_of_service="https://example.com/terms/",
)

# Register exception handlers for custom exceptions
app.add_exception_handler(YTMusicServiceException, ytmusic_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# Uncomment to catch all unhandled exceptions (recommended for production)
# app.add_exception_handler(Exception, generic_exception_handler)

# Register slowapi rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

if settings.ENABLE_COMPRESSION:
    app.add_middleware(GZipMiddleware, minimum_size=1000)

cors_origins = ["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(",")
cors_methods = ["*"] if settings.CORS_ALLOW_METHODS == "*" else settings.CORS_ALLOW_METHODS.split(",")
cors_headers = ["*"] if settings.CORS_ALLOW_HEADERS == "*" else settings.CORS_ALLOW_HEADERS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    summary="Root endpoint",
    description="Endpoint raíz con información del servicio y enlaces a documentación.",
    response_description="Información del servicio",
    responses={
        200: {
            "description": "Servicio online",
            "content": {
                "application/json": {
                    "example": {
                        "status": "online",
                        "service": "YouTube Music Service",
                        "version": "1.0.0",
                        "auth": "Browser",
                        "docs": "/docs",
                        "api": "/api/v1"
                    }
                }
            }
        }
    },
    tags=["general"]
)
async def root():
    """Endpoint raíz con información del servicio."""
    logger.debug("Root endpoint accessed")
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "auth": "Browser",
        "docs": "/docs",
        "api": settings.API_V1_STR
    }


@app.get(
    "/health",
    summary="Health check",
    description="Verifica el estado de salud del servicio. Usado por sistemas de monitoreo y Docker health checks.",
    response_description="Estado de salud",
    responses={
        200: {
            "description": "Servicio saludable",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        }
    },
    tags=["general"]
)
async def health_check():
    """Health check endpoint para monitoreo."""
    return {"status": "healthy"}
