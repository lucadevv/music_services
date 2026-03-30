# Music Services (YouTube Music API)

API REST construida con **FastAPI** que wrappinga `ytmusicapi` + `yt-dlp` para proveer endpoints de búsqueda, browse, streaming y más sobre YouTube Music.

Diseñada para ser consumida por un backend NestJS dentro de un monorepo.

- 🔍 **Búsqueda**: Canciones, videos, álbumes, artistas, playlists
- 🎧 **Streaming**: URLs directas de audio (best quality)
- 📱 **Navegación**: Artistas, álbumes, canciones, letras
- 🔑 **Browser Admin**: Configuración de autenticación desde panel admin

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
[API Layer] → app/api/v1/endpoints/*.py (33 endpoints)
    ↓
[Service Layer] → app/services/*.py (lógica de negocio + @cache_result para metadata)
    ↓
[Core Layer] → Redis cache (service-level only), Circuit Breaker, Exceptions
    ↓
[External] → ytmusicapi (metadata) + yt-dlp (stream URLs, runtime)
```

**Nota**: `/explore/category/{params}` está deprecado y es un alias de `/explore/moods/{params}`.

### Cache Architecture

El sistema usa un **two-tier caching strategy**:

| Layer | Qué se cachea | TTL | Key Pattern |
|-------|---------------|-----|-------------|
| **Service** (`@cache_result`) | Metadata (canciones, álbumes, playlists, etc.) | 1-24h | `music:{method}:{hash}` |
| **Stream** (`StreamService`) | Stream URLs (audio directo) | 1h | `music:stream:url:{video_id}` |

**Regla de oro**: Las stream URLs **NUNCA** se cachean dentro de respuestas de endpoint. Siempre se inyectan en runtime via `stream_service.enrich_items_with_streams()`.

Esto elimina los 403 que ocurrían cuando YouTube expira las URLs (~6h) y el endpoint cache las servía stale.

## Endpoints (33)

### Search

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/search/` | Search music content |
| GET | `/search/suggestions` | Get search suggestions |
| DELETE | `/search/suggestions` | Remove search suggestion |

### Browse

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/browse/home` | Get home page |
| GET | `/browse/artist/{channel_id}/albums` | Get artist albums |
| GET | `/browse/album/{album_id}` | Get album info |
| GET | `/browse/album/{album_id}/browse-id` | Get album browse ID |
| GET | `/browse/song/{video_id}` | Get song metadata |
| GET | `/browse/song/{video_id}/related` | Get related songs |
| GET | `/browse/lyrics/{browse_id}` | Get lyrics |
| GET | `/browse/lyrics-by-video/{video_id}` | Get lyrics by video |

### Explore

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/explore/` | Get explore content |
| GET | `/explore/moods` | Get mood categories |
| GET | `/explore/moods/{params}` | Get mood playlists |
| GET | `/explore/charts` | Get charts |
| GET | `/explore/category/{params}` | ⚠️ DEPRECATED — alias for `/moods/{params}` |

### Stream

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/stream/{video_id}` | Get audio stream URL |
| GET | `/stream/proxy/{video_id}` | Proxy audio stream |
| GET | `/stream/batch` | Batch stream URLs |
| GET | `/stream/cache/stats` | Cache statistics |
| DELETE | `/stream/cache` | Clear stream cache |
| GET | `/stream/cache/info/{video_id}` | Check cached URL |
| DELETE | `/stream/cache/{video_id}` | Delete cached URL |
| GET | `/stream/status/{video_id}` | Check if URL cached |

### Watch

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/watch/` | Watch playlist (radio) |

### Playlists

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/playlists/{playlist_id}` | Get playlist |

### Podcasts

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/podcasts/channel/{channel_id}` | Get podcast channel |
| GET | `/podcasts/channel/{channel_id}/episodes` | Get channel episodes |
| GET | `/podcasts/{browse_id}` | Get podcast |
| GET | `/podcasts/episode/{browse_id}` | Get episode |
| ~~GET~~ | ~~`/podcasts/episodes/{browse_id}/playlist`~~ | ~~Get episodes playlist~~ ⚠️ DEPRECATED |

### Autenticación

El servicio separa autenticación de **música** y **admin**:

- Endpoints de música (`/search`, `/browse`, `/explore`, `/playlists`, `/watch`, `/stream/{video_id}`, `/stream/proxy/{video_id}`, `/stream/batch`, `/podcasts`) requieren:
  - `Authorization: Bearer <api_key>`
- Endpoints de admin (`/auth/*`, `/api-keys/*`, `/stats/*`, `/stream/cache*`, `/stream/status/*`) requieren:
  - `X-Admin-Key: <ADMIN_SECRET_KEY>`

Ejemplo para endpoints de música:

```bash
curl -H "Authorization: Bearer sk_live_tu_api_key" \
  "http://localhost:8000/api/v1/search/?q=eminem"
```

### Endpoints de Autenticación (`/api/v1/auth/*`)

**API Keys** - Gestión de claves API con rotación y control granular:

1. **POST /auth/api-keys** - Crear nueva API key
2. **GET /auth/api-keys** - Listar todas las API keys
3. **GET /auth/api-keys/{key_id}** - Obtener API key específica
4. **PATCH /auth/api-keys/{key_id}** - Actualizar API key (título, habilitado/inhabilitado)
5. **DELETE /auth/api-keys/{key_id}** - Eliminar API key
6. **POST /auth/api-keys/verify** - Verificar si una API key es válida

**Browser Authentication** - Gestión de cuentas de YouTube Music:

1. **POST /auth/browser/from-url** - Agregar cuenta desde URL
2. **POST /auth/browser/from-headers** - Agregar cuenta desde headers
3. **GET /auth/browser** - Listar cuentas
4. **DELETE /auth/browser/{account_name}** - Eliminar cuenta
5. **POST /auth/browser/test** - Probar autenticación
6. **GET /auth/status** - Estado de autenticación

### Primer Uso

**Al iniciar el servicio por primera vez:**

1. Configurá `ADMIN_SECRET_KEY` en tu `.env`
2. Usá ese valor en el header `X-Admin-Key` para todos los endpoints de admin

**Crear nuevas API keys:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "X-Admin-Key: your-admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"title": "Mobile App"}'
```

**Respuesta:**
```json
{
  "key_id": "abc123def456",
  "api_key": "sk_live_1a2b3c4d5e6f7g8h9i0j",
  "title": "Mobile App",
  "enabled": true,
  "created_at": "2026-03-29T10:00:00Z",
  "is_master": false
}
```

**Usar API key:**
```bash
curl http://localhost:8000/api/v1/auth/browser \
  -H "X-Admin-Key: your-admin-secret-key"
```

### Retrocompatibilidad

`ADMIN_SECRET_KEY` es obligatorio para endpoints de admin. Las API keys de base de datos se usan para consumo de endpoints de música.

### Stats

| Method | Route | Summary |
|--------|-------|---------|
| GET | `/stats/stats` | Service statistics |

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
- Referencia rápida endpoints + schemas: `docs/SWAGGER_REFERENCE.md`

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

## Fixes Recientes

| Ticket | Endpoint | Problema | Solución |
|--------|----------|----------|----------|
| SCRUM-32 | `/browse/album/{id}/browse-id` | 500 cuando ytmusicapi retorna None | Fallback a `get_album` para extraer `audioPlaylistId` |
| SCRUM-33 | `/stats/stats` | 500 por ImportError si Redis no disponible | Graceful degradation con error informativo |
| SCRUM-34 | `/explore/category/{params}` | ytmusicapi deprecado | Alias de `/explore/moods/{params}` con header `Warning: 299` |
| SCRUM-35 | `/browse/artist/{id}/albums` | 500 por rate limit (429) | Retry (2 intentos) + fallback via `get_artist()` |

## Licencia

Privado - Uso interno
