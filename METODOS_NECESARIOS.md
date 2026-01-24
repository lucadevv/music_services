# Métodos de ytmusicapi Necesarios para App de Música (Usuario Final)

> **Objetivo**: App de música para usuario final que solo consume contenido público.
> **NO incluye**: Biblioteca personal, suscripciones, álbumes guardados, gestión de playlists personales.

## ✅ MÉTODOS NECESARIOS (Contenido Público)

### 🔍 Search (Búsqueda)
- ✅ `YTMusic.search()` - Buscar canciones, álbumes, artistas, playlists
- ✅ `YTMusic.get_search_suggestions()` - Sugerencias de búsqueda
- ❌ `YTMusic.remove_search_suggestions()` - No necesario (gestión personal)

### 🏠 Browsing (Navegación Pública)
- ✅ `YTMusic.get_home()` - Página principal con contenido destacado
- ✅ `YTMusic.get_artist(channel_id)` - Información de artista
- ✅ `YTMusic.get_artist_albums(channel_id)` - Álbumes del artista
- ✅ `YTMusic.get_album(album_id)` - Información de álbum
- ✅ `YTMusic.get_album_browse_id(album_id)` - ID de navegación del álbum
- ✅ `YTMusic.get_song(video_id)` - Metadatos de canción
- ✅ `YTMusic.get_song_related(video_id)` - Canciones relacionadas
- ✅ `YTMusic.get_lyrics(browse_id)` - Letras de canciones
- ❌ `YTMusic.get_user(channel_id)` - No necesario (usuarios específicos)
- ❌ `YTMusic.get_user_playlists(channel_id)` - No necesario (playlists de usuarios)
- ❌ `YTMusic.get_user_videos(channel_id)` - No necesario (videos de usuarios)
- ❌ `YTMusic.get_tasteprofile()` - No necesario (perfil personal)
- ❌ `YTMusic.set_tasteprofile()` - No necesario (configuración personal)

### 🎵 Explore (Exploración)
- ✅ `YTMusic.get_mood_categories()` - Categorías de moods y géneros
- ✅ `YTMusic.get_mood_playlists(params)` - Playlists por mood/género
- ✅ `YTMusic.get_charts(country)` - Charts (top songs, trending)

### ▶️ Watch (Reproducción)
- ✅ `YTMusic.get_watch_playlist()` - Playlist de reproducción (radio, shuffle, siguiente)

### 📋 Playlists (Listas Públicas)
- ✅ `YTMusic.get_playlist(playlist_id)` - Obtener playlist pública (canciones)
- ❌ `YTMusic.create_playlist()` - No necesario (creación personal)
- ❌ `YTMusic.edit_playlist()` - No necesario (edición personal)
- ❌ `YTMusic.delete_playlist()` - No necesario (eliminación personal)
- ❌ `YTMusic.add_playlist_items()` - No necesario (modificación personal)
- ❌ `YTMusic.remove_playlist_items()` - No necesario (modificación personal)

### 🎙️ Podcasts (Opcional)
- ✅ `YTMusic.get_channel(channel_id)` - Información de canal de podcast
- ✅ `YTMusic.get_channel_episodes(channel_id)` - Episodios del canal
- ✅ `YTMusic.get_podcast(browse_id)` - Información de podcast
- ✅ `YTMusic.get_episode(browse_id)` - Información de episodio
- ✅ `YTMusic.get_episodes_playlist(browse_id)` - Playlist de episodios

## ❌ MÉTODOS NO NECESARIOS (Biblioteca Personal)

### 📚 Library (Biblioteca Personal)
- ❌ `YTMusic.get_library_playlists()` - Playlists guardadas del usuario
- ❌ `YTMusic.get_library_songs()` - Canciones guardadas del usuario
- ❌ `YTMusic.get_library_albums()` - Álbumes guardados del usuario
- ❌ `YTMusic.get_library_artists()` - Artistas guardados del usuario
- ❌ `YTMusic.get_library_subscriptions()` - Suscripciones del usuario
- ❌ `YTMusic.get_library_podcasts()` - Podcasts guardados del usuario
- ❌ `YTMusic.get_library_channels()` - Canales guardados del usuario
- ❌ `YTMusic.get_liked_songs()` - Canciones que me gustan
- ❌ `YTMusic.get_saved_episodes()` - Episodios guardados
- ❌ `YTMusic.get_history()` - Historial de reproducción
- ❌ `YTMusic.add_history_item()` - Agregar al historial
- ❌ `YTMusic.remove_history_items()` - Eliminar del historial
- ❌ `YTMusic.rate_song()` - Calificar canción
- ❌ `YTMusic.edit_song_library_status()` - Editar estado en biblioteca
- ❌ `YTMusic.rate_playlist()` - Calificar playlist
- ❌ `YTMusic.subscribe_artists()` - Suscribirse a artistas
- ❌ `YTMusic.unsubscribe_artists()` - Desuscribirse de artistas
- ❌ `YTMusic.get_account_info()` - Información de cuenta

### 📤 Uploads (Subidas Personales)
- ❌ `YTMusic.get_library_upload_songs()` - Canciones subidas
- ❌ `YTMusic.get_library_upload_artists()` - Artistas subidos
- ❌ `YTMusic.get_library_upload_albums()` - Álbumes subidos
- ❌ `YTMusic.get_library_upload_artist(artist_id)` - Artista subido específico
- ❌ `YTMusic.get_library_upload_album(album_id)` - Álbum subido específico
- ❌ `YTMusic.upload_song()` - Subir canción
- ❌ `YTMusic.delete_upload_entity()` - Eliminar entidad subida

## 📊 Resumen

### Métodos Necesarios: ~20 métodos
1. **Search**: 2 métodos (search, suggestions)
2. **Browsing**: 8 métodos (home, artist, album, song, lyrics, related)
3. **Explore**: 3 métodos (mood_categories, mood_playlists, charts)
4. **Watch**: 1 método (watch_playlist)
5. **Playlists**: 1 método (get_playlist - solo lectura)
6. **Podcasts**: 5 métodos (opcional, pero útil)

### Métodos NO Necesarios: ~25 métodos
- Todos los de Library (biblioteca personal)
- Todos los de Uploads (subidas personales)
- Crear/editar/eliminar playlists
- Calificar canciones/playlists
- Suscripciones personales
- Historial personal
- Perfil de gustos

## 🎯 Endpoints Actuales vs Necesarios

### ✅ Ya Implementados Correctamente:
- ✅ `/api/v1/search` - Búsqueda
- ✅ `/api/v1/explore` - Exploración (moods, charts)
- ✅ `/api/v1/browse` - Navegación (artistas, álbumes, canciones)
- ✅ `/api/v1/playlists/{id}` - Obtener playlist (solo lectura)
- ✅ `/api/v1/watch` - Playlists de reproducción
- ✅ `/api/v1/stream/{videoId}` - Stream de audio
- ✅ `/api/v1/podcasts` - Podcasts (opcional)

### ❌ Simplificados (Correcto):
- ✅ `/api/v1/library` - Solo endpoint informativo
- ✅ `/api/v1/uploads` - Solo endpoint informativo

### ✅ Estado Actual:
- ✅ Todos los métodos necesarios están implementados
- ✅ Playlists solo permite lectura (GET)
- ✅ Endpoints de gestión personal eliminados (user, tasteprofile)
- ✅ Library y Uploads simplificados (solo informativos)

## 📋 Lista Final de Métodos Necesarios

### Para App de Música (Usuario Final):

1. **Search** (2 métodos)
   - `search()` ✅
   - `get_search_suggestions()` ✅

2. **Browsing** (6 métodos)
   - `get_home()` ✅
   - `get_artist(channel_id)` ✅
   - `get_artist_albums(channel_id)` ✅
   - `get_album(album_id)` ✅
   - `get_song(video_id)` ✅
   - `get_song_related(video_id)` ✅
   - `get_lyrics(browse_id)` ✅

3. **Explore** (3 métodos)
   - `get_mood_categories()` ✅
   - `get_mood_playlists(params)` ✅ (con fallback a búsqueda)
   - `get_charts(country)` ✅

4. **Watch** (1 método)
   - `get_watch_playlist()` ✅

5. **Playlists** (1 método - solo lectura)
   - `get_playlist(playlist_id)` ✅

6. **Podcasts** (5 métodos - opcional)
   - `get_channel(channel_id)` ✅
   - `get_channel_episodes(channel_id)` ✅
   - `get_podcast(browse_id)` ✅
   - `get_episode(browse_id)` ✅
   - `get_episodes_playlist(browse_id)` ✅

**Total: ~18 métodos esenciales para app de música pública**
