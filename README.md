# YouTube Music API Service

Servicio API profesional de YouTube Music construido con FastAPI siguiendo las mejores prácticas de arquitectura.

## 🏗️ Arquitectura

El proyecto sigue los patrones de **fastapi-templates** con:

- **Separación de responsabilidades**: Services, Endpoints, Core
- **Dependency Injection**: Uso de `Depends()` de FastAPI
- **Async Patterns**: Todas las operaciones son asíncronas
- **Configuración centralizada**: Settings con Pydantic
- **Estructura modular**: Fácil de mantener y escalar

## 📁 Estructura del Proyecto

```
app/
├── api/                    # API routes
│   └── v1/
│       ├── endpoints/      # Endpoints por funcionalidad
│       │   ├── browse.py
│       │   ├── explore.py
│       │   ├── search.py
│       │   ├── library.py
│       │   ├── playlists.py
│       │   ├── watch.py
│       │   ├── podcasts.py
│       │   ├── uploads.py
│       │   └── stream.py
│       └── router.py        # Router principal
├── core/                   # Configuración core
│   ├── config.py          # Settings
│   └── ytmusic_client.py   # Cliente YTMusic
├── services/               # Lógica de negocio
│   ├── browse_service.py
│   ├── explore_service.py
│   ├── search_service.py
│   ├── library_service.py
│   ├── playlist_service.py
│   ├── watch_service.py
│   ├── podcast_service.py
│   ├── upload_service.py
│   └── stream_service.py
└── main.py                 # Aplicación FastAPI
```

## 🚀 Instalación

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

Crea un archivo `.env` (opcional) o usa las configuraciones por defecto:

```env
BROWSER_JSON_PATH=browser.json
OAUTH_JSON_PATH=oauth.json  # Opcional
HOST=0.0.0.0
PORT=8000
```

## 🎵 Funcionalidades Principales (Contenido Público)

### Explore (Explorar) - ⭐ Principal para app de música
- `GET /api/v1/explore/` - Contenido completo: moods, géneros, charts
  - Retorna: `moods_genres` (con `params`), `charts` (top_songs, trending)
  - **Flujo**: Obtén categorías → usa `params` → obtén playlists → obtén canciones
  
- `GET /api/v1/explore/moods` - Categorías de moods/géneros
  - Cada categoría tiene un campo `params`
  - **Ejemplo**: `{"title": "Workout", "params": "ggMPOg1uX1JOQWZFeDByc2Jm"}`
  
- `GET /api/v1/explore/moods/{params}` - Playlists de un mood/género
  - Usa el `params` de una categoría para obtener sus playlists
  - Cada playlist tiene un `playlistId` para obtener canciones
  
- `GET /api/v1/explore/charts` - Top songs y trending
  - Opcional: `?country=PE` para charts por país
  - Cada canción tiene `videoId` para obtener stream
  
- `GET /api/v1/explore/category/{category_params}` - Alias de moods/{params}

### Browse (Navegación)
- `GET /api/v1/browse/home` - Página principal
- `GET /api/v1/browse/artist/{channel_id}` - Información de artista
- `GET /api/v1/browse/artist/{channel_id}/albums` - Álbumes del artista
- `GET /api/v1/browse/album/{album_id}` - Información de álbum
- `GET /api/v1/browse/song/{video_id}` - Metadatos de canción
- `GET /api/v1/browse/song/{video_id}/related` - Canciones relacionadas
- `GET /api/v1/browse/lyrics/{browse_id}` - Letras de canciones

### Search (Búsqueda)
- `GET /api/v1/search/?q={query}` - Buscar contenido
  - Parámetros: `filter`, `scope`, `limit`, `ignore_spelling`
- `GET /api/v1/search/suggestions?q={query}` - Sugerencias de búsqueda
- `DELETE /api/v1/search/suggestions?q={query}` - Eliminar sugerencias

### Library (Biblioteca Personal)
⚠️ **Nota**: Los endpoints de library requieren autenticación de usuario y son para contenido personal guardado en la cuenta. Para una app de música pública, usa los endpoints de `/explore` en su lugar.

- `GET /api/v1/library/` - Información sobre endpoints de library

### Playlists (Listas de reproducción)
- `GET /api/v1/playlists/{playlist_id}` - ⭐ Obtener playlist pública (canciones)
  - Usa el `playlistId` de una playlist obtenida en `/explore/moods/{params}`
  - Retorna las canciones de la playlist con sus `videoId` para stream
  
- `POST /api/v1/playlists/` - Crear playlist (requiere auth)
- `PATCH /api/v1/playlists/{playlist_id}` - Editar playlist (requiere auth)
- `DELETE /api/v1/playlists/{playlist_id}` - Eliminar playlist (requiere auth)
- `POST /api/v1/playlists/{playlist_id}/items` - Agregar items (requiere auth)
- `DELETE /api/v1/playlists/{playlist_id}/items` - Eliminar items (requiere auth)

### Watch (Reproducción)
- `GET /api/v1/watch/?video_id={id}` - Playlist de reproducción
- `GET /api/v1/watch/?playlist_id={id}&radio=true` - Radio playlist
- `GET /api/v1/watch/?playlist_id={id}&shuffle=true` - Shuffle playlist

### Podcasts
- `GET /api/v1/podcasts/channel/{channel_id}` - Información de canal
- `GET /api/v1/podcasts/channel/{channel_id}/episodes` - Episodios del canal
- `GET /api/v1/podcasts/{browse_id}` - Información de podcast
- `GET /api/v1/podcasts/episode/{browse_id}` - Información de episodio
- `GET /api/v1/podcasts/episodes/{browse_id}/playlist` - Playlist de episodios

### Uploads (Subidas)
⚠️ **Nota**: Los endpoints de uploads requieren autenticación y son para gestionar contenido personal subido.

- `GET /api/v1/uploads/` - Información sobre endpoints de uploads

### Stream (Audio) - ⭐ Para reproducir música
- `GET /api/v1/stream/{video_id}` - URL de stream de audio
  - Usa el `videoId` de cualquier canción (charts, playlists, search)
  - Retorna: `url` (stream directo), `title`, `artist`, `duration`, `thumbnail`

## 🏃 Ejecución

```bash
python servicio_ytmusic.py
```

O directamente con uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 Documentación

Una vez ejecutando, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Root**: http://localhost:8000/

## 🔧 Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **ytmusicapi**: API no oficial de YouTube Music
- **yt-dlp**: Descarga y extracción de streams
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

## 🔄 Flujo de Uso Recomendado para App de Música

### 1. Obtener Contenido para Explorar
```bash
GET /api/v1/explore/
```
Retorna: moods/géneros (con `params`), charts (top songs con `videoId`)

### 2. Obtener Playlists de un Género/Mood
```bash
GET /api/v1/explore/moods/{params}
```
Usa el `params` de una categoría del paso 1. Retorna playlists con `playlistId`.

### 3. Obtener Canciones de una Playlist
```bash
GET /api/v1/playlists/{playlist_id}
```
Usa el `playlistId` del paso 2. Retorna canciones con `videoId`.

### 4. Obtener Stream de Audio
```bash
GET /api/v1/stream/{video_id}
```
Usa el `videoId` de cualquier canción. Retorna URL de stream directo.

### 5. Buscar Música
```bash
GET /api/v1/search/?q={query}&filter=songs
```
Retorna canciones con `videoId` para stream.

## 📝 Notas

- Requiere `browser.json` con las cookies de autenticación de YouTube Music
- **Para app de música pública**: Usa principalmente `/explore`, `/search`, `/browse`, `/playlists/{id}`, y `/stream/{videoId}`
- Los endpoints de library y uploads requieren autenticación y son para contenido personal
- El servicio usa async/await para mejor rendimiento
- Todos los endpoints siguen el patrón RESTful

## 🎯 Mejores Prácticas Implementadas

✅ Separación de responsabilidades (Services, Endpoints, Core)  
✅ Dependency Injection con FastAPI  
✅ Async patterns en todas las operaciones  
✅ Configuración centralizada con Pydantic Settings  
✅ Manejo de errores consistente  
✅ Documentación automática con FastAPI  
✅ Estructura modular y escalable  
