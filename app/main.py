"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import get_settings
from app.api.v1.router import api_router
import time

settings = get_settings()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri="memory://"
)

# Custom rate limit handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
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
    # Startup
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"📡 API available at http://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}")
    print(f"⚡ Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    print(f"💾 Caching: {'Enabled' if settings.CACHE_ENABLED else 'Disabled'}")
    print(f"🗜️  Compression: {'Enabled' if settings.ENABLE_COMPRESSION else 'Disabled'}")
    yield
    # Shutdown
    print(f"👋 Shutting down {settings.PROJECT_NAME}")


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

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Compression middleware (reduce bandwidth)
if settings.ENABLE_COMPRESSION:
    app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
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

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API router
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
                        "auth": "browser.json",
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
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "auth": "browser.json",
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
