# Music Services (YouTube Music API)

API REST construida con **FastAPI** que wrappinga `ytmusicapi` + `yt-dlp` para proveer endpoints de búsqueda, browse, streaming y más sobre YouTube Music.

Diseñada para ser consumida por un backend NestJS dentro de un monorepo.

## Stack

| Componente | Tecnología |
|------------|-----------|
| Framework | FastAPI |
| Lenguaje | Python 3.11 |
| YouTube Music | ytmusicapi |
| Streaming | yt-dlp |
| Cache | Redis 7 (service-layer only) |
| Rate Limiting | slowapi |
| Validación | Pydantic v2 |
| Containerización | Docker + Compose |

## Arquitectura

```
HTTP Request
    ↓
[Middleware] → CORS, GZip, Rate Limiting (slowapi+Redis)
    ↓
[API Layer] → app/api/v1/endpoints/*.py (~35 endpoints)
    ↓
[Service Layer] → app/services/*.py (lógica de negocio + @cache_result para metadata)
    ↓
[Core Layer] → Redis cache (service-level only), Circuit Breaker, Exceptions
    ↓
[External] → ytmusicapi (metadata) + yt-dlp (stream URLs, runtime)
```

### Cache Architecture

El sistema usa un **two-tier caching strategy**:

| Layer | Qué se cachea | TTL | Key Pattern |
|-------|---------------|-----|-------------|
| **Service** (`@cache_result`) | Metadata (canciones, álbumes, playlists, etc.) | 1-24h | `music:{method}:{hash}` |
| **Stream** (`StreamService`) | Stream URLs (audio directo) | 1h | `music:stream:url:{video_id}` |

**Regla de oro**: Las stream URLs **NUNCA** se cachean dentro de respuestas de endpoint. Siempre se inyectan en runtime via `stream_service.enrich_items_with_streams()`.

Esto elimina los 403 que ocurrían cuando YouTube expira las URLs (~6h) y el endpoint cache las servía stale.

## Endpoints (~35)


| Dominio | Endpoints |
|---------|-----------|
| `/search` | Búsqueda, sugerencias |
| `/browse` | Home, artista, álbum, canción, lyrics, related |
| `/explore` | Charts, moods/genres |
| `/stream` | URL streaming, proxy de audio, batch, cache |
| `/watch` | Playlist radio/shuffle |
| `/playlists` | Playlists públicas |
| `/podcasts` | Canales, episodios |
| `/stats` | Monitoreo del servicio |
| `/auth` | Administración de OAuth (credenciales, flujo de autorización, estado) |

## Requisitos Previos

- Python 3.9+
- Redis 7
- Credenciales OAuth de Google Cloud (YouTube Data API v3)

## Instalación Rápida

```bash
# Clonar
git clone <repo-url>
cd music_services

# Entorno virtual
python3 -m venv venv
source venv/bin/activate

# Dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus credenciales OAuth
```

## Configuración OAuth

Ver [README_OAUTH.md](./README_OAUTH.md) para la guía completa de configuración de credenciales.

Resumen rápido:

1. Crear OAuth Client ID en [Google Cloud Console](https://console.cloud.google.com/) (tipo: TVs and Limited Input Devices)
2. Habilitar **YouTube Data API v3**
3. Configurar credenciales en `.env`:

```env
YTMUSIC_CLIENT_ID=tu_client_id.apps.googleusercontent.com
YTMUSIC_CLIENT_SECRET=tu_client_secret
```

4. Generar `oauth.json`:

```bash
python scripts/generate_oauth.py
```

## API de Autenticación OAuth

El servicio incluye endpoints de administración para configurar la autenticación de YouTube Music desde un panel admin. Consulta la [documentación completa](./README_AUTH_API.md) para detalles sobre los endpoints `/api/v1/auth/*` (guardar credenciales, iniciar flujo OAuth, verificar autorización, etc.).

La especificación OpenAPI está disponible en:
- JSON: `/openapi.json`
- YAML: `/openapi.yaml`

## Levantar el servicio

```bash
# Desarrollo (con hot reload)
docker-compose --profile dev up -d

# Producción
docker-compose up -d

# Solo local (sin Docker)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host de escucha |
| `PORT` | `8000` | Puerto |
| `CORS_ORIGINS` | `*` | Orígenes permitidos |
| `RATE_LIMIT_ENABLED` | `true` | Activar rate limiting |
| `RATE_LIMIT_PER_MINUTE` | `60` | Requests por minuto por IP |
| `CACHE_ENABLED` | `true` | Activar caché Redis |
| `CACHE_BACKEND` | `memory` | Backend de caché (memory/redis) |
| `REDIS_HOST` | `localhost` | Host de Redis |
| `REDIS_PORT` | `6379` | Puerto de Redis |
| `YTMUSIC_CLIENT_ID` | - | OAuth Client ID |
| `YTMUSIC_CLIENT_SECRET` | - | OAuth Client Secret |

## Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requiere Redis corriendo)
pytest tests/integration/ -v

# Todos con coverage
pytest --cov=app tests/ -v
```

## Estructura del Proyecto

```
music_services/
├── app/
│   ├── api/v1/endpoints/    # Routers (~10 dominios)
│   ├── core/                # Config, cache, exceptions, validators
│   ├── schemas/             # Pydantic response models
│   ├── services/            # Lógica de negocio
│   └── main.py              # Entry point FastAPI
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/                 # Scripts utilitarios
├── Dockerfile
├── docker-compose.yml
└── docker-compose.dev.yml
```

## Licencia

Privado - Uso interno
