# Endpoints que Retornan `stream_url`

## 📋 Resumen

Los siguientes endpoints retornan `stream_url` en el JSON de respuesta cuando `include_stream_urls=true` (por defecto `true`):

## 🎵 Endpoints con `stream_url`

### 1. **GET `/api/v1/search/`** - Búsqueda
**Parámetro**: `include_stream_urls` (default: `true`)

**Retorna `stream_url` cuando**:
- `filter` es `songs`, `videos`, o `None`
- `include_stream_urls=true`

**Ejemplo de respuesta**:
```json
{
  "results": [
    {
      "videoId": "rMbATaj7Il8",
      "title": "Song Title",
      "artists": [{"name": "Artist"}],
      "stream_url": "https://rr5---sn-...",
      "thumbnail": "https://i.ytimg.com/vi/.../maxresdefault.jpg"
    }
  ],
  "query": "search query"
}
```

---

### 2. **GET `/api/v1/explore/`** - Exploración
**Parámetro**: `include_stream_urls` (default: `true`)

**Retorna `stream_url` en**:
- `charts.top_songs` - Canciones top
- `charts.trending` - Canciones trending

**Ejemplo de respuesta**:
```json
{
  "moods_genres": [...],
  "home": [...],
  "charts": {
    "top_songs": [
      {
        "videoId": "rMbATaj7Il8",
        "title": "Song Title",
        "stream_url": "https://rr5---sn-...",
        "thumbnail": "https://..."
      }
    ],
    "trending": [...]
  }
}
```

---

### 3. **GET `/api/v1/explore/charts`** - Charts
**Parámetro**: `include_stream_urls` (default: `true`)

**Retorna `stream_url` en**:
- `top_songs` - Canciones top
- `trending` - Canciones trending

**Ejemplo de respuesta**:
```json
{
  "top_songs": [
    {
      "videoId": "rMbATaj7Il8",
      "title": "Song Title",
      "stream_url": "https://rr5---sn-...",
      "thumbnail": "https://..."
    }
  ],
  "trending": [...]
}
```

---

### 4. **GET `/api/v1/browse/album/{album_id}`** - Álbum
**Parámetro**: `include_stream_urls` (default: `true`)

**Retorna `stream_url` en**:
- `tracks[]` - Cada track del álbum

**Ejemplo de respuesta**:
```json
{
  "title": "Album Title",
  "artists": [{"name": "Artist"}],
  "tracks": [
    {
      "videoId": "rMbATaj7Il8",
      "title": "Track Title",
      "stream_url": "https://rr5---sn-...",
      "thumbnail": "https://..."
    }
  ]
}
```

---

### 5. **GET `/api/v1/browse/song/{video_id}/related`** - Canciones relacionadas
**Parámetro**: `include_stream_urls` (default: `true`)

**Retorna `stream_url` en**:
- `related_songs[]` - Canciones relacionadas

**Ejemplo de respuesta**:
```json
{
  "related_songs": [
    {
      "videoId": "rMbATaj7Il8",
      "title": "Related Song",
      "stream_url": "https://rr5---sn-...",
      "thumbnail": "https://..."
    }
  ]
}
```

---

### 6. **GET `/api/v1/playlists/{playlist_id}`** - Playlist
**Parámetro**: `include_stream_urls` (default: `true`)

**Retorna `stream_url` en**:
- `tracks[]` - Cada track de la playlist

**Ejemplo de respuesta**:
```json
{
  "title": "Playlist Title",
  "trackCount": 50,
  "tracks": [
    {
      "videoId": "rMbATaj7Il8",
      "title": "Track Title",
      "artists": [{"name": "Artist"}],
      "stream_url": "https://rr5---sn-...",
      "thumbnail": "https://..."
    }
  ]
}
```

---

### 7. **GET `/api/v1/watch/`** - Watch Playlist
**Parámetro**: `include_stream_urls` (default: `true`)

**Retorna `stream_url` en**:
- `tracks[]` o `items[]` - Canciones de la playlist de reproducción

**Ejemplo de respuesta**:
```json
{
  "tracks": [
    {
      "videoId": "rMbATaj7Il8",
      "title": "Next Song",
      "stream_url": "https://rr5---sn-...",
      "thumbnail": "https://..."
    }
  ]
}
```

---

### 8. **GET `/api/v1/stream/{video_id}`** - Stream directo
**Este endpoint SIEMPRE retorna `stream_url`** (no tiene parámetro `include_stream_urls`)

**Retorna**:
- `url` - URL directa de stream de audio
- `title` - Título
- `artist` - Artista
- `duration` - Duración en segundos
- `thumbnail` - Thumbnail en mejor calidad

**Ejemplo de respuesta**:
```json
{
  "title": "Song Title",
  "artist": "Artist Name",
  "duration": 180,
  "thumbnail": "https://i.ytimg.com/vi/.../maxresdefault.jpg",
  "url": "https://rr5---sn-..."
}
```

---

## ⚙️ Control del Parámetro

Todos los endpoints (excepto `/api/v1/stream/{video_id}`) tienen el parámetro opcional:

- **`include_stream_urls`** (query parameter)
  - **Default**: `true`
  - **Tipo**: `boolean`
  - **Uso**: 
    - `?include_stream_urls=true` → Incluye `stream_url` y `thumbnail` mejorado
    - `?include_stream_urls=false` → NO incluye `stream_url` (solo metadatos originales)

## 📝 Notas Importantes

1. **`stream_url` solo se agrega a items que tienen `videoId`**
2. **Todos los metadatos originales se preservan** - `stream_url` y `thumbnail` se agregan sin reemplazar campos existentes
3. **Caché inteligente**: 
   - Metadatos: 1 día TTL
   - Stream URLs: 4 horas TTL
4. **Circuit breaker**: Protege contra rate limiting de YouTube

## 🔗 Ejemplos de Uso

```bash
# Búsqueda con stream_url
curl "http://localhost:8000/api/v1/search/?q=test&filter=songs&include_stream_urls=true"

# Búsqueda sin stream_url (más rápido)
curl "http://localhost:8000/api/v1/search/?q=test&filter=songs&include_stream_urls=false"

# Playlist con stream_url
curl "http://localhost:8000/api/v1/playlists/PL...?include_stream_urls=true"

# Stream directo (siempre retorna url)
curl "http://localhost:8000/api/v1/stream/rMbATaj7Il8"
```
