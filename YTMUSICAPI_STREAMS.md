# 📊 Análisis: ytmusicapi para Streams

## 🔍 Investigación sobre ytmusicapi y Streams

### Métodos Disponibles en ytmusicapi

Según la documentación oficial de ytmusicapi, **NO hay un método directo** para obtener URLs de stream de audio.

#### Métodos relacionados con reproducción:

1. **`get_watch_playlist()`** ✅ (Ya implementado)
   - Retorna lista de canciones para reproducir
   - Incluye `videoId` de cada canción
   - **NO incluye URLs de stream directo**
   - Solo metadatos: título, artista, duración, `videoId`

2. **`get_song(video_id)`** ✅ (Ya implementado)
   - Retorna metadatos de la canción
   - Incluye información del video
   - **NO incluye URL de stream**

### Conclusión sobre ytmusicapi

**ytmusicapi NO expone URLs de stream directamente.**

- `ytmusicapi` está diseñado para obtener **metadatos** y **listas de reproducción**
- Para obtener URLs de stream, necesitas usar `yt-dlp` (como ya lo haces)
- `ytmusicapi` y `yt-dlp` son complementarios:
  - `ytmusicapi`: Metadatos, búsqueda, playlists
  - `yt-dlp`: URLs de stream de audio/video

## 🎯 Estrategia Actual vs Alternativa

### Estrategia Actual (yt-dlp) ✅
```python
# Usar yt-dlp para obtener URL de stream
yt_dlp.YoutubeDL().extract_info(url, download=False)
# Retorna: URL directo de audio
```

**Ventajas:**
- ✅ Obtiene URL de stream directo
- ✅ Funciona bien
- ✅ Soporta múltiples formatos de audio

**Desventajas:**
- ❌ Hace petición HTTP a YouTube por cada video
- ❌ Más propenso a rate limiting
- ❌ Requiere `browser.json` separado

### Alternativa (usar get_watch_playlist)
```python
# Usar ytmusicapi.get_watch_playlist()
# Retorna: Lista con videoIds
# Luego usar yt-dlp solo cuando sea necesario
```

**Ventajas:**
- ✅ Usa la misma sesión que otros endpoints
- ✅ Menos peticiones (solo cuando se necesita stream)

**Desventajas:**
- ❌ Aún necesitas `yt-dlp` para obtener el URL
- ❌ No elimina el problema de rate limiting

## 💡 Recomendación

**Mantener la estrategia actual con mejoras:**

1. ✅ **Caché agresivo** (Ya implementado)
   - Reduce peticiones repetidas al mismo video
   - TTL de 10 minutos

2. ✅ **Circuit breaker** (Ya implementado)
   - Detecta rate limiting
   - Pausa automáticamente cuando YouTube limita

3. 🔄 **Optimización futura: Pool de sesiones**
   - Múltiples `browser.json` para distribuir carga
   - Rotación entre sesiones

## 📝 Nota sobre get_watch_playlist

El método `get_watch_playlist()` de ytmusicapi:
- Retorna canciones con `videoId`
- **NO retorna URLs de stream**
- Es útil para obtener "siguiente canción" o "radio"
- Pero aún necesitas usar `yt-dlp` para obtener el URL de stream

## 🎯 Conclusión

**No hay alternativa mejor que yt-dlp para streams.**

La mejor estrategia es:
1. ✅ Caché agresivo (implementado)
2. ✅ Circuit breaker (implementado)
3. 🔄 Pool de sesiones (siguiente paso)
4. 🔄 Throttling interno (opcional)

ytmusicapi no puede reemplazar a yt-dlp para obtener URLs de stream.
