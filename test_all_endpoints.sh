#!/bin/bash
# Script para ejecutar todos los curls de testeo

BASE_URL="http://localhost:8000"
ADMIN_KEY="Aa123456"
API_VERSION="/api/v1"

echo "=========================================="
echo "🚀 TESTING COMPLETO DE API DE YOUTUBE MUSIC"
echo "=========================================="
echo ""

# Obtener video_id de prueba
echo "📍 PASO 1: Obtener video_id de prueba"
echo "------------------------------------------"
curl -s "${BASE_URL}${API_VERSION}/explore/charts?country=US" | jq -r '.charts.top_songs[0].videoId // "rMbATaj7Il8"'
VIDEO_ID=$(curl -s "${BASE_URL}${API_VERSION}/explore/charts?country=US" | jq -r '.charts.top_songs[0].videoId // "rMbATaj7Il8"')
echo "Video ID: $VIDEO_ID"
echo ""

# Tabla 1: Todos los Endpoints
echo "=========================================="
echo "📋 TABLA 1: Todos los Endpoints"
echo "=========================================="
echo "| ID | Endpoint | Método | Requiere Auth | Grupo | Descripción | Status |"
echo "|----|----------|--------|---------------|-------|-------------|--------|"

echo "| 1 | / | GET | ❌ | General | Endpoint raíz |"
curl -s -w "\n%{http_code}" "${BASE_URL}/" | jq -r ".status" | head -1
echo ""

echo "| 2 | /api/v1/auth/status | GET | ✅ | Auth | Estado de autenticación |"
curl -s -w "\n%{http_code}" -H "X-Admin-Key: ${ADMIN_KEY}" "${BASE_URL}${API_VERSION}/auth/status" | jq -r ".detail" | head -1
echo ""

echo "| 3 | /api/v1/auth/credentials | GET | ✅ | Auth | Consultar estado de credenciales |"
curl -s -w "\n%{http_code}" -H "X-Admin-Key: ${ADMIN_KEY}" "${BASE_URL}${API_VERSION}/auth/credentials" | jq -r ".detail" | head -1
echo ""

echo "| 4 | /api/v1/auth/credentials | POST | ✅ | Auth | Guardar credenciales OAuth |"
curl -s -w "\n%{http_code}" -H "X-Admin-Key: ${ADMIN_KEY}" -H "Content-Type: application/json" -d '{"client_id":"test_id","client_secret":"test_secret"}' "${BASE_URL}${API_VERSION}/auth/credentials" | jq -r ".detail" | head -1
echo ""

echo "| 5 | /api/v1/auth/oauth/start | POST | ✅ | Auth | Iniciar flujo OAuth |"
curl -s -w "\n%{http_code}" -H "X-Admin-Key: ${ADMIN_KEY}" -H "Content-Type: application/json" -d '{}' "${BASE_URL}${API_VERSION}/auth/oauth/start" | jq -r ".detail" | head -1
echo ""

echo "| 6 | /api/v1/auth/oauth/poll | POST | ✅ | Auth | Verificar autorización OAuth |"
curl -s -w "\n%{http_code}" -H "X-Admin-Key: ${ADMIN_KEY}" -H "Content-Type: application/json" -d '{"session_id":"550e8400-e29b-41d4-a716-446655440000"}' "${BASE_URL}${API_VERSION}/auth/oauth/poll" | jq -r ".detail" | head -1
echo ""

echo "| 7 | /api/v1/browse/home | GET | ❌ | Browse | Get home page |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/home" | jq -r '.error_code' | head -1
echo ""

echo "| 8 | /api/v1/browse/album/{album_id} | GET | ❌ | Browse | Get album information |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/album/MPREb123456" | jq -r '.error_code' | head -1
echo ""

echo "| 9 | /api/v1/browse/song/{video_id} | GET | ❌ | Browse | Get song metadata |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/song/${VIDEO_ID}" | jq -r '.error_code' | head -1
echo ""

echo "| 10 | /api/v1/browse/song/{video_id}/related | GET | ❌ | Browse | Get related songs |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/song/${VIDEO_ID}?include_stream_urls=true" | jq -r '.error_code' | head -1
echo ""

echo "| 11 | /api/v1/browse/album/{album_id}/browse-id | GET | ❌ | Browse | Get album browse ID |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/album/browse-id/MPREb123456" | jq -r '.detail' | head -1
echo ""

echo "| 12 | /api/v1/browse/lyrics/{browse_id} | GET | ❌ | Browse | Get lyrics by browse ID |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/lyrics/VL1234567890" | jq -r '.error_code' | head -1
echo ""

echo "| 13 | /api/v1/browse/lyrics-by-video/{video_id} | GET | ❌ | Browse | Get lyrics by video ID |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/lyrics-by-video/${VIDEO_ID}" | jq -r '.error' | head -1
echo ""

echo "| 14 | /api/v1/browse/artist/{channel_id}/albums | GET | ❌ | Browse | Get artist albums |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/browse/artist/albums/UC1234567890" | jq -r '.detail' | head -1
echo ""

echo "| 15 | /api/v1/explore/ | GET | ❌ | Explore | Obtener contenido de exploración |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/explore/" | jq -r '.error_code' | head -1
echo ""

echo "| 16 | /api/v1/explore/moods | GET | ❌ | Explore | Obtener moods y géneros |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/explore/moods" | jq -r '.error_code' | head -1
echo ""

echo "| 17 | /api/v1/explore/moods/{params} | GET | ❌ | Explore | Obtener playlists de mood/género |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/explore/moods/test_params" | jq -r '.detail' | head -1
echo ""

echo "| 18 | /api/v1/explore/charts | GET | ❌ | Explore | Obtener charts |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/explore/charts?country=US" | jq -r '.error_code' | head -1
echo ""

echo "| 19 | /api/v1/explore/category/{category_params} | GET | ❌ | Explore | Alias para /explore/moods (deprecated) |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/explore/category/test_params" | jq -r '.detail' | head -1
echo ""

echo "| 20 | /api/v1/search/ | GET | ❌ | Search | Buscar contenido musical |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/search/?q=cumbia&limit=10" | jq -r '.error_code' | head -1
echo ""

echo "| 21 | /api/v1/search/suggestions | GET | ❌ | Search | Obtener sugerencias de búsqueda |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/search/suggestions?q=cumb" | jq -r '.error_code' | head -1
echo ""

echo "| 22 | /api/v1/search/suggestions | DELETE | ❌ | Search | Eliminar sugerencia de búsqueda |"
curl -s -w "\n%{http_code}" -X DELETE "${BASE_URL}${API_VERSION}/search/suggestions?q=cumb" | jq -r '.error_code' | head -1
echo ""

echo "| 23 | /api/v1/playlists/{playlist_id} | GET | ❌ | Playlists | Obtener información de playlist |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/playlists/PL1234567890ABCDEF" | jq -r '.error_code' | head -1
echo ""

echo "| 24 | /api/v1/watch/ | GET | ❌ | Watch | Obtener playlist de reproducción |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/watch?video_id=${VIDEO_ID}&limit=25"
echo ""

echo "| 25 | /api/v1/podcasts/channel/{channel_id} | GET | ❌ | Podcasts | Obtener información de canal de podcast |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/podcasts/channel/UC1234567890/test" | jq -r '.detail' | head -1
echo ""

echo "| 26 | /api/v1/podcasts/channel/{channel_id}/episodes | GET | ❌ | Podcasts | Obtener episodios de canal |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/podcasts/channel/episodes/UC1234567890/test" | jq -r '.detail' | head -1
echo ""

echo "| 27 | /api/v1/podcasts/{browse_id} | GET | ❌ | Podcasts | Obtener información de podcast |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/podcasts/VL1234567890" | jq -r '.error_code' | head -1
echo ""

echo "| 28 | /api/v1/podcasts/episode/{browse_id} | GET | ❌ | Podcasts | Obtener información de episodio |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/podcasts/episode/VL1234567890" | jq -r '.error_code' | head -1
echo ""

echo "| 29 | /api/v1/podcasts/episodes/{browse_id}/playlist | GET | ❌ | Podcasts | Obtener playlist de episodios |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/podcasts/episodes/playlist/VL1234567890" | jq -r '.detail' | head -1
echo ""

echo "| 30 | /api/v1/stream/{video_id} | GET | ❌ | Stream | Obtener stream URL |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/stream/${VIDEO_ID}" | jq -r '.streamUrl' | head -1
echo ""

echo "| 31 | /api/v1/stream/batch | GET | ❌ | Stream | Obtener URLs de stream para múltiples videos |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/stream/batch?ids=${VIDEO_ID},TEST123" | jq -r '.results[0].videoId' | head -1
echo ""

echo "| 32 | /api/v1/stream/status/{video_id} | GET | ❌ | Stream | Verificar si URL de stream está en cache |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/stream/status/${VIDEO_ID}" | jq -r '.cached' | head -1
echo ""

echo "| 33 | /api/v1/stream/cache/info/{video_id} | GET | ❌ | Stream | Verificar cache de stream |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_version}/stream/cache/info/${VIDEO_ID}" | jq -r '.error' | head -1
echo ""

echo "| 34 | /api/v1/stream/cache/{video_id} | DELETE | ❌ | Stream | Eliminar cache de stream |"
curl -s -w "\n%{http_code}" -X DELETE "${BASE_URL}${API_VERSION}/stream/cache/${VIDEO_ID}" | jq -r '.deleted' | head -1
echo ""

echo "| 35 | /api/v1/stream/cache/stats | GET | ❌ | Stream | Mostrar estadísticas de cache |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/stream/cache/stats" | jq -r '.keys_count' | head -1
echo ""

echo "| 36 | /api/v1/stream/proxy/{video_id} | GET | ❌ | Stream | Proxy de streaming de audio |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/stream/proxy/${VIDEO_ID}" --output /dev/null
echo ""

echo "| 37 | /api/v1/stats/stats | GET | ❌ | Stats | Obtener estadísticas del servicio |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/stats/stats" | jq -r '.service' | head -1
echo ""

echo "| 38 | /api/v1/uploads | GET | ❌ | Uploads | Información sobre endpoints de uploads (no implementado) |"
curl -s -w "\n%{http_code}" "${BASE_URL}${API_VERSION}/uploads" | jq -r '.detail' | head -1
echo ""

echo "=========================================="
echo "✅ TESTING COMPLETADO"
echo "=========================================="
