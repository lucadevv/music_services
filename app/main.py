"""Main FastAPI application."""
# Standard library
import time
import json
from pathlib import Path
from contextlib import asynccontextmanager

# Third-party
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import yaml

# Local imports
from app.core.auth_middleware import AuthMiddleware
from app.core.config import get_settings

# Increase thread pool for heavy IO operations
import concurrent.futures
import asyncio
# Standard pool is min(32, os.cpu_count() + 4) which is too small for 100+ concurrent extractions
loop = asyncio.get_event_loop()
loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=200))

from app.core.logging_config import setup_logging, get_logger
from app.core.exceptions import YTMusicServiceException
from app.core.exception_handlers import (
    validation_exception_handler,
    generic_exception_handler,
)
from app.api.v1.router import api_router
from app.core.background_cache import cache_manager
from app.core.ytmusic_client import is_authenticated

# Setup logging first
setup_logging()
logger = get_logger(__name__)

settings = get_settings()


def get_effective_ip(request: Request) -> str:
    """Return the client's real IP, honoring X-Forwarded-For when behind proxies."""
    # Try X-Forwarded-For header first (when behind proxy/load balancer)
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    # Last resort: unknown
    return "unknown"


# Rate limiting con Redis para entornos distribuidos
# Usa Redis como storage para que funcione con múltiples instancias
storage_uri = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
limiter = Limiter(
    key_func=get_effective_ip,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri=storage_uri
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
    
    # Initialize database
    from app.core.database import init_db
    await init_db()
    logger.info("✅ Database initialized")
    
    # Initialize admin API key from env
    from app.core.database import create_admin_key_from_env
    await create_admin_key_from_env()
    
    # Iniciar gestor de cache en background
    await cache_manager.start()
    
    yield
    
    # Detener gestor de cache
    await cache_manager.stop()
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


tags_metadata = [
    {
        "name": "Music",
        "description": "Endpoints para búsqueda, navegación y streaming de contenido musical.",
    },
    {
        "name": "Admin",
        "description": "Endpoints administrativos para gestión de llaves, caché y estadísticas.",
    },
    {
        "name": "general",
        "description": "Endpoints básicos del sistema y salud.",
    }
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
🚀 **YouTube Music API Service** - Servicio de alto rendimiento para YouTube Music.

Este servicio proporciona una interfaz unificada para buscar música, navegar por artistas y álbumes, gestionar listas de reproducción y obtener streams de audio directo.

### 📚 Características Principales
- 🔍 **Búsqueda Avanzada**: Canciones, álbumes, artistas y playlists.
- 🎧 **Streaming Directo**: Obtención de URLs de audio de alta calidad.
- 🛡️ **Resiliencia**: Circuit breaker y rate limiting integrados.
- ⚡ **Rendimiento**: Caché inteligente en Redis y compresión GZip.
### 🔐 Seguridad y Autenticación

El servicio utiliza dos métodos de autenticación dependiendo del tipo de endpoint:

1.  **Endpoints de Música (`/api/v1/music/*`)**:
    -   Requieren una **API Key** válida.
    -   Se debe enviar en la cabecera: `Authorization: Bearer <tu_api_key>`.
    -   Puedes gestionar tus llaves en la sección de Admin.

2.  **Endpoints de Administración (`/api/v1/admin/*`)**:
    -   Requieren la **Master Admin Key** configurada en el servidor.
    -   Se debe enviar en la cabecera: `X-Admin-Key: <admin_secret_key>`.
    -   Estos endpoints NO aceptan Bearer tokens por seguridad.
    """,
    openapi_tags=tags_metadata,
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
@app.exception_handler(YTMusicServiceException)
async def ytmusic_exception_handler(request: Request, exc: YTMusicServiceException):
    """Manejador para excepciones específicas del servicio YTMusic."""
    logger.error(f"🔥 YTMusicServiceException [{exc.status_code}]: {exc.message} - Details: {exc.details}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register slowapi rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

if settings.ENABLE_COMPRESSION:
    app.add_middleware(GZipMiddleware, minimum_size=1000)

cors_origins = ["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(",")
cors_methods = ["*"] if settings.CORS_ALLOW_METHODS == "*" else settings.CORS_ALLOW_METHODS.split(",")
cors_headers = ["*"] if settings.CORS_ALLOW_HEADERS == "*" else settings.CORS_ALLOW_HEADERS.split(",")

app.add_middleware(AuthMiddleware)

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


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """Add caching headers for GET requests."""
    response = await call_next(request)
    
    # Only cache GET requests
    if request.method == "GET" and response.status_code == 200:
        path = request.url.path
        
        # Don't cache endpoints that might have user-specific data
        if not any(x in path for x in ["/stats", "/history", "/suggestions"]):
            # Cache based on endpoint type
            if "/search" in path:
                response.headers["Cache-Control"] = "public, max-age=300"  # 5 min
            elif "/explore" in path or "/charts" in path:
                response.headers["Cache-Control"] = "public, max-age=1800"  # 30 min
            elif "/playlists/" in path or "/album/" in path:
                response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
            elif "/stream/" in path or "/watch" in path:
                # Stream URLs shouldn't be cached at HTTP level (Redis handles this)
                pass
    
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
                        "auth": "browser",
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
        "auth": "browser",
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
    return {
        "status": "healthy",
        "authenticated": is_authenticated(),
    }


limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer(auto_error=False)


def custom_openapi():
    """Custom OpenAPI schema with Bearer auth."""
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("custom_openapi called - generating schema")
    
    # Always regenerate to ensure security is included
    app.openapi_schema = None
    openapi_schema = app.openapi()
    
    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "API Key para endpoints de música. Obtén una en /api/v1/admin/api-keys/"
        },
        "AdminKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Admin-Key",
            "description": "Master Admin Key configurada en el servidor para gestión administrativa."
        }
    }

    # Assign security to paths based on prefix
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, config in methods.items():
            if path.startswith(f"{settings.API_V1_STR}/admin/"):
                config["security"] = [{"AdminKey": []}]
            elif path.startswith(f"{settings.API_V1_STR}/music/"):
                config["security"] = [{"BearerAuth": []}]
            else:
                config["security"] = []

    # Cache the modified schema
    app.openapi_schema = openapi_schema
    
    logger.warning("Schema generated with security")
    
    return openapi_schema


# Generate the custom schema at module load time
custom_openapi()


app.add_api_route("/openapi.yaml", custom_openapi, include_in_schema=False)


@app.get("/openapi.json", include_in_schema=False)
async def openapi_json():
    """Serve OpenAPI specification as JSON."""
    # Return the pre-generated schema with security
    return JSONResponse(content=app.openapi_schema)
