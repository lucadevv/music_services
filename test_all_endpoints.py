#!/usr/bin/env python3
"""
Script de testing completo para la API de YouTube Music
Ejecuta curl a todos los endpoints y genera reporte
"""
import subprocess
import json
import time
import re
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
ADMIN_KEY = "Aa123456"
API_VERSION = "/api/v1"

# Resultados
results = []
endpoints_list = []
passing_endpoints = []
failing_endpoints = []
inconsistencies = []

# ============================================
# FUNCIÓN PARA EJECUTAR CURL
# ============================================
def execute_curl(method, endpoint, headers=None, data=None):
    """Ejecuta un curl y retorna código de estado y respuesta"""

    # Construir comando
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method, f"{BASE_URL}{endpoint}"]

    # Headers
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

    # Data para POST/PUT
    if data:
        cmd.extend(["-H", "Content-Type: application/json"])
        cmd.extend(["-d", json.dumps(data)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        status_code = result.stderr.strip().split('\n')[-1] if result.stderr.strip().split('\n') else "000"

        # Parsear respuesta (si tiene JSON)
        try:
            response = json.loads(output)
        except json.JSONDecodeError:
            response = {"raw_output": output[:200]}  # Primeros 200 chars

        return status_code, response

    except subprocess.TimeoutExpired:
        return "TIMEOUT", {"error": "Request timed out"}
    except Exception as e:
        return "ERROR", {"error": str(e)}

# ============================================
# FUNCIÓN PARA GENERAR TABLAS
# ============================================
def generate_table(endpoints, columns):
    """Genera tabla Markdown con los resultados"""
    if not endpoints:
        return "| ID | " + " | ".join(columns) + " |\n|---|" + "|---|".join(["---"] * len(columns)) + "|\n"

    headers = "| ID | " + " | ".join(columns) + " |"
    separator = "|---|" + "|---|".join(["---"] * len(columns)) + "|"

    table = headers + "\n" + separator + "\n"

    for i, ep in enumerate(endpoints, 1):
        row = [str(i)] + [str(ep.get(col, "")) for col in columns]
        table += "| " + " | ".join(row) + " |\n"

    return table

# ============================================
# ============================================
# EJECUCIÓN DE TESTS
# ============================================
# ============================================

print("=" * 80)
print("🚀 INICIANDO TESTING COMPLETO DE API DE YOUTUBE MUSIC")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Admin Key: {ADMIN_KEY}")
print(f"API Version: {API_VERSION}")
print("=" * 80)
print()

# ============================================
# 1. OBTENER VIDEO_ID DE PRUEBA
# ============================================
print("📍 PASO 1: Obtener video_id de prueba desde /explore/charts")
print("-" * 80)

status_code, response = execute_curl("GET", f"{API_VERSION}/explore/charts?country=US")
print(f"GET {API_VERSION}/explore/charts?country=US")
print(f"Status: {status_code}")
print(f"Response: {json.dumps(response, indent=2)[:300]}...")
print()

if status_code == "200":
    try:
        video_id = response.get("charts", {}).get("top_songs", [{}])[0].get("videoId")
        if video_id:
            print(f"✅ Video ID obtenido: {video_id}")
            print()
        else:
            print("❌ No se encontró videoId en response")
            video_id = "rMbATaj7Il8"  # Fallback
            print(f"⚠️  Usando video_id de fallback: {video_id}")
    except:
        print("❌ Error al parsear response")
        video_id = "rMbATaj7Il8"  # Fallback
        print(f"⚠️  Usando video_id de fallback: {video_id}")
else:
    print(f"❌ Error al obtener video_id. Status: {status_code}")
    video_id = "rMbATaj7Il8"  # Fallback
    print(f"⚠️  Usando video_id de fallback: {video_id}")

print()
print("=" * 80)
print()

# ============================================
# 2. TEST DE HEALTH CHECK
# ============================================
print("🏥 TEST 1: Health Check")
print("-" * 80)

endpoint_info = {
    "endpoint": "/",
    "method": "GET",
    "requires_auth": False,
    "group": "General",
    "description": "Endpoint raíz con información del servicio"
}

status_code, response = execute_curl("GET", "/")
pass_fail = "✅ PASÓ" if status_code in ["200", "201"] else "❌ FALLÓ"
print(f"{pass_fail} - {endpoint_info['description']}")
print(f"  Status: {status_code}")
print(f"  Response: {json.dumps(response, indent=2)[:200]}")
print()

results.append({
    **endpoint_info,
    "status_code": status_code,
    "response": response,
    "result": pass_fail
})
endpoints_list.append(endpoint_info)
if status_code in ["200", "201"]:
    passing_endpoints.append(endpoint_info)
else:
    failing_endpoints.append(endpoint_info)

# ============================================
# 3. TEST AUTH ENDPOINTS
# ============================================
print("🔐 TESTS GRUPO: Auth (5 endpoints)")
print("=" * 80)

auth_endpoints = [
    {
        "endpoint": "/auth/status",
        "method": "GET",
        "requires_auth": True,
        "group": "Auth",
        "description": "Estado de autenticación"
    },
    {
        "endpoint": "/auth/credentials",
        "method": "GET",
        "requires_auth": True,
        "group": "Auth",
        "description": "Consultar estado de credenciales"
    },
    {
        "endpoint": "/auth/credentials",
        "method": "POST",
        "requires_auth": True,
        "group": "Auth",
        "description": "Guardar credenciales OAuth",
        "data": {"client_id": "test_id", "client_secret": "test_secret"}
    },
    {
        "endpoint": "/auth/oauth/start",
        "method": "POST",
        "requires_auth": True,
        "group": "Auth",
        "description": "Iniciar flujo OAuth",
        "data": {}
    },
    {
        "endpoint": "/auth/oauth/poll",
        "method": "POST",
        "requires_auth": True,
        "group": "Auth",
        "description": "Verificar autorización OAuth",
        "data": {"session_id": "550e8400-e29b-41d4-a716-446655440000"}
    }
]

for ep in auth_endpoints:
    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        f"{API_VERSION}{ep['endpoint']}",
        headers=headers,
        data=ep.get("data")
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "202", "204"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {API_VERSION}{ep['endpoint']}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "202", "204"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 4. TEST BROWSE ENDPOINTS
# ============================================
print("🎵 TESTS GRUPO: Browse (8 endpoints)")
print("=" * 80)

browse_endpoints = [
    {
        "endpoint": "/browse/home",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get home page"
    },
    {
        "endpoint": "/browse/album",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get album information",
        "requires_id": "album_id"
    },
    {
        "endpoint": "/browse/song",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get song metadata",
        "requires_id": "video_id"
    },
    {
        "endpoint": "/browse/song",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get related songs",
        "requires_id": "video_id",
        "query_params": {"include_stream_urls": "true"}
    },
    {
        "endpoint": "/browse/album/browse-id",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get album browse ID",
        "requires_id": "album_id"
    },
    {
        "endpoint": "/browse/lyrics",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get lyrics by browse ID",
        "requires_id": "browse_id"
    },
    {
        "endpoint": "/browse/lyrics-by-video",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get lyrics by video ID",
        "requires_id": "video_id"
    },
    {
        "endpoint": f"/browse/artist/albums",
        "method": "GET",
        "requires_auth": False,
        "group": "Browse",
        "description": "Get artist albums",
        "requires_id": "channel_id"
    }
]

for ep in browse_endpoints:
    # Construir URL
    url = f"{API_VERSION}{ep['endpoint']}"

    # Agregar ID si requiere
    if ep.get("requires_id"):
        id_value = ep["requires_id"].replace("_id", "").upper()
        if id_value == "VIDEO":
            url += f"/{video_id}"
        elif id_value == "ALBUM":
            url += f"/MPREb123456"  # Album_id dummy
        elif id_value == "CHANNEL":
            url += f"/UC1234567890"  # channel_id dummy
        elif id_value == "BROWSE":
            url += f"/VL1234567890"  # browse_id dummy

    # Agregar query params si los hay
    if ep.get("query_params"):
        url += "?" + "&".join([f"{k}={v}" for k, v in ep["query_params"].items()])

    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        url,
        headers=headers
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {url}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "204"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 5. TEST EXPLORE ENDPOINTS
# ============================================
print("🔍 TESTS GRUPO: Explore (5 endpoints)")
print("=" * 80)

explore_endpoints = [
    {
        "endpoint": "/explore/",
        "method": "GET",
        "requires_auth": False,
        "group": "Explore",
        "description": "Obtener contenido de exploración"
    },
    {
        "endpoint": "/explore/moods",
        "method": "GET",
        "requires_auth": False,
        "group": "Explore",
        "description": "Obtener moods y géneros"
    },
    {
        "endpoint": "/explore/moods/params",
        "method": "GET",
        "requires_auth": False,
        "group": "Explore",
        "description": "Obtener playlists de mood/género",
        "requires_id": "params"
    },
    {
        "endpoint": "/explore/charts",
        "method": "GET",
        "requires_auth": False,
        "group": "Explore",
        "description": "Obtener charts",
        "query_params": {"country": "US"}
    },
    {
        "endpoint": "/explore/category/params",
        "method": "GET",
        "requires_auth": False,
        "group": "Explore",
        "description": "Alias para /explore/moods (deprecated)",
        "requires_id": "params"
    }
]

for ep in explore_endpoints:
    # Construir URL
    url = f"{API_VERSION}{ep['endpoint']}"

    # Agregar ID si requiere
    if ep.get("requires_id"):
        url += f"/test_params"

    # Agregar query params
    if ep.get("query_params"):
        url += "?" + "&".join([f"{k}={v}" for k, v in ep["query_params"].items()])

    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        url,
        headers=headers
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {url}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "204"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 6. TEST SEARCH ENDPOINTS
# ============================================
print("🔎 TESTS GRUPO: Search (3 endpoints)")
print("=" * 80)

search_endpoints = [
    {
        "endpoint": "/search/",
        "method": "GET",
        "requires_auth": False,
        "group": "Search",
        "description": "Buscar contenido musical",
        "query_params": {"q": "cumbia", "limit": "10"}
    },
    {
        "endpoint": "/search/suggestions",
        "method": "GET",
        "requires_auth": False,
        "group": "Search",
        "description": "Obtener sugerencias de búsqueda",
        "query_params": {"q": "cumb"}
    },
    {
        "endpoint": "/search/suggestions",
        "method": "DELETE",
        "requires_auth": False,
        "group": "Search",
        "description": "Eliminar sugerencia de búsqueda",
        "query_params": {"q": "cumb"}
    }
]

for ep in search_endpoints:
    # Construir URL
    url = f"{API_VERSION}{ep['endpoint']}"

    # Agregar query params
    if ep.get("query_params"):
        url += "?" + "&".join([f"{k}={v}" for k, v in ep["query_params"].items()])

    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        url,
        headers=headers
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204", "202"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {url}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "204", "202"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 7. TEST PLAYLISTS ENDPOINT
# ============================================
print("📀 TESTS GRUPO: Playlists (1 endpoint)")
print("=" * 80)

playlist_endpoints = [
    {
        "endpoint": "/playlists",
        "method": "GET",
        "requires_auth": False,
        "group": "Playlists",
        "description": "Obtener información de playlist",
        "requires_id": "playlist_id"
    }
]

for ep in playlist_endpoints:
    # Construir URL
    url = f"{API_VERSION}{ep['endpoint']}"

    # Agregar ID si requiere
    if ep.get("requires_id"):
        url += f"/PL1234567890ABCDEF"

    # Agregar query params
    if ep.get("query_params"):
        url += "?" + "&".join([f"{k}={v}" for k, v in ep["query_params"].items()])

    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        url,
        headers=headers
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {url}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "204"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 8. TEST WATCH ENDPOINT
# ============================================
print("🎬 TESTS GRUPO: Watch (1 endpoint)")
print("=" * 80)

watch_endpoints = [
    {
        "endpoint": "/watch",
        "method": "GET",
        "requires_auth": False,
        "group": "Watch",
        "description": "Obtener playlist de reproducción",
        "query_params": {"video_id": video_id, "limit": "25"}
    }
]

for ep in watch_endpoints:
    # Construir URL
    url = f"{API_VERSION}{ep['endpoint']}"

    # Agregar query params
    if ep.get("query_params"):
        url += "?" + "&".join([f"{k}={v}" for k, v in ep["query_params"].items()])

    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        url,
        headers=headers
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {url}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "204"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 9. TEST PODCASTS ENDPOINTS
# ============================================
print("🎙️ TESTS GRUPO: Podcasts (5 endpoints)")
print("=" * 80)

podcast_endpoints = [
    {
        "endpoint": "/podcasts/channel",
        "method": "GET",
        "requires_auth": False,
        "group": "Podcasts",
        "description": "Obtener información de canal de podcast",
        "requires_id": "channel_id"
    },
    {
        "endpoint": "/podcasts/channel/episodes",
        "method": "GET",
        "requires_auth": False,
        "group": "Podcasts",
        "description": "Obtener episodios de canal",
        "requires_id": "channel_id"
    },
    {
        "endpoint": "/podcasts",
        "method": "GET",
        "requires_auth": False,
        "group": "Podcasts",
        "description": "Obtener información de podcast",
        "requires_id": "browse_id"
    },
    {
        "endpoint": "/podcasts/episode",
        "method": "GET",
        "requires_auth": False,
        "group": "Podcasts",
        "description": "Obtener información de episodio",
        "requires_id": "browse_id"
    },
    {
        "endpoint": "/podcasts/episodes/playlist",
        "method": "GET",
        "requires_auth": False,
        "group": "Podcasts",
        "description": "Obtener playlist de episodios",
        "requires_id": "browse_id"
    }
]

for ep in podcast_endpoints:
    # Construir URL
    url = f"{API_VERSION}{ep['endpoint']}"

    # Agregar ID si requiere
    if ep.get("requires_id"):
        if "channel" in ep["endpoint"]:
            url += f"/UC1234567890/test"
        else:
            url += f"/VL1234567890"

    # Agregar query params
    if ep.get("query_params"):
        url += "?" + "&".join([f"{k}={v}" for k, v in ep["query_params"].items()])

    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        url,
        headers=headers
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {url}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "204"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 10. TEST STREAM ENDPOINTS
# ============================================
print("🎧 TESTS GRUPO: Stream (8 endpoints)")
print("=" * 80)

stream_endpoints = [
    {
        "endpoint": "/stream",
        "method": "GET",
        "requires_auth": False,
        "group": "Stream",
        "description": "Obtener stream URL",
        "requires_id": "video_id"
    },
    {
        "endpoint": "/stream/batch",
        "method": "GET",
        "requires_auth": False,
        "group": "Stream",
        "description": "Obtener URLs de stream para múltiples videos",
        "query_params": {"ids": f"{video_id},TEST123"}
    },
    {
        "endpoint": "/stream/status",
        "method": "GET",
        "requires_auth": False,
        "group": "Stream",
        "description": "Verificar si URL de stream está en cache",
        "requires_id": "video_id"
    },
    {
        "endpoint": "/stream/cache/info",
        "method": "GET",
        "requires_auth": False,
        "group": "Stream",
        "description": "Verificar cache de stream",
        "requires_id": "video_id"
    },
    {
        "endpoint": "/stream/cache",
        "method": "DELETE",
        "requires_auth": False,
        "group": "Stream",
        "description": "Eliminar cache de stream",
        "requires_id": "video_id"
    },
    {
        "endpoint": "/stream/cache/stats",
        "method": "GET",
        "requires_auth": False,
        "group": "Stream",
        "description": "Mostrar estadísticas de cache"
    },
    {
        "endpoint": "/stream/proxy",
        "method": "GET",
        "requires_auth": False,
        "group": "Stream",
        "description": "Proxy de streaming de audio",
        "requires_id": "video_id"
    }
]

for ep in stream_endpoints:
    # Construir URL
    url = f"{API_VERSION}{ep['endpoint']}"

    # Agregar ID si requiere
    if ep.get("requires_id"):
        url += f"/{video_id}"

    # Agregar query params
    if ep.get("query_params"):
        url += "?" + "&".join([f"{k}={v}" for k, v in ep["query_params"].items()])

    headers = {"X-Admin-Key": ADMIN_KEY} if ep["requires_auth"] else {}

    endpoint_info = {
        **ep,
        "id": len(endpoints_list) + 1
    }

    status_code, response = execute_curl(
        ep["method"],
        url,
        headers=headers
    )

    pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204"] else "❌ FALLÓ"
    print(f"{pass_fail} - {ep['description']}")
    print(f"  Endpoint: {ep['method']} {url}")
    print(f"  Status: {status_code}")
    print(f"  Response: {json.dumps(response, indent=2)[:200]}")
    print()

    results.append({
        **endpoint_info,
        "status_code": status_code,
        "response": response,
        "result": pass_fail
    })
    endpoints_list.append(endpoint_info)
    if status_code in ["200", "201", "204"]:
        passing_endpoints.append(endpoint_info)
    else:
        failing_endpoints.append(endpoint_info)

print("=" * 80)
print()

# ============================================
# 11. TEST STATS ENDPOINT
# ============================================
print("📊 TESTS GRUPO: Stats (1 endpoint)")
print("=" * 80)

stats_endpoint = {
    "endpoint": "/stats/stats",
    "method": "GET",
    "requires_auth": False,
    "group": "Stats",
    "description": "Obtener estadísticas del servicio"
}

status_code, response = execute_curl(
    stats_endpoint["method"],
    f"{API_VERSION}{stats_endpoint['endpoint']}"
)

pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204"] else "❌ FALLÓ"
print(f"{pass_fail} - {stats_endpoint['description']}")
print(f"  Endpoint: {stats_endpoint['method']} {API_VERSION}{stats_endpoint['endpoint']}")
print(f"  Status: {status_code}")
print(f"  Response: {json.dumps(response, indent=2)[:200]}")
print()

results.append({
    **stats_endpoint,
    "status_code": status_code,
    "response": response,
    "result": pass_fail
})
endpoints_list.append(stats_endpoint)
if status_code in ["200", "201", "204"]:
    passing_endpoints.append(stats_endpoint)
else:
    failing_endpoints.append(stats_endpoint)

print("=" * 80)
print()

# ============================================
# 12. TEST UPLOADS ENDPOINT
# ============================================
print("📤 TEST GRUPO: Uploads (1 endpoint)")
print("=" * 80)

uploads_endpoint = {
    "endpoint": "/uploads",
    "method": "GET",
    "requires_auth": False,
    "group": "Uploads",
    "description": "Información sobre endpoints de uploads (no implementado)"
}

status_code, response = execute_curl(
    uploads_endpoint["method"],
    f"{API_VERSION}{uploads_endpoint['endpoint']}"
)

pass_fail = "✅ PASÓ" if status_code in ["200", "201", "204", "501"] else "❌ FALLÓ"
print(f"{pass_fail} - {uploads_endpoint['description']}")
print(f"  Endpoint: {uploads_endpoint['method']} {API_VERSION}{uploads_endpoint['endpoint']}")
print(f"  Status: {status_code}")
print(f"  Response: {json.dumps(response, indent=2)[:200]}")
print()

results.append({
    **uploads_endpoint,
    "status_code": status_code,
    "response": response,
    "result": pass_fail
})
endpoints_list.append(uploads_endpoint)
if status_code in ["200", "201", "204", "501"]:
    passing_endpoints.append(uploads_endpoint)
else:
    failing_endpoints.append(uploads_endpoint)

print("=" * 80)
print()

# ============================================
# ============================================
# GENERACIÓN DE REPORTES
# ============================================
# ============================================

print("=" * 80)
print("📊 GENERANDO REPORTES FINALES")
print("=" * 80)
print()

# Tabla 1: Todos los Endpoints
table1 = generate_table(endpoints_list, ["ID", "Endpoint", "Método", "Requiere Auth", "Grupo", "Descripción", "Result"])

with open("test_results_table1_all_endpoints.md", "w") as f:
    f.write("# Tabla 1: Todos los Endpoints\n\n")
    f.write("```markdown\n")
    f.write(table1)
    f.write("```\n")

print("✅ Tabla 1: Todos los Endpoints - Creada: test_results_table1_all_endpoints.md")
print()

# Tabla 2: Endpoints que Pasan
table2 = generate_table(passing_endpoints, ["ID", "Endpoint", "Método", "Descripción"])

with open("test_results_table2_passing.md", "w") as f:
    f.write("# Tabla 2: Endpoints que Pasan\n\n")
    f.write("```markdown\n")
    f.write(table2)
    f.write("```\n")

print("✅ Tabla 2: Endpoints que Pasan - Creada: test_results_table2_passing.md")
print()

# Tabla 3: Endpoints que Fallan
table3 = generate_table(failing_endpoints, ["ID", "Endpoint", "Método", "Status Code", "Descripción"])

with open("test_results_table3_failing.md", "w") as f:
    f.write("# Tabla 3: Endpoints que Fallan\n\n")
    f.write("```markdown\n")
    f.write(table3)
    f.write("```\n")

print("✅ Tabla 3: Endpoints que Fallan - Creada: test_results_table3_failing.md")
print()

# Tabla 4: Inconsistencias
inconsistency_data = []

# Check for inconsistencies in auth requirements
auth_endpoints_test = [ep for ep in endpoints_list if ep["group"] == "Auth" and ep["requires_auth"]]
if len(auth_endpoints_test) > 0:
    missing_auth = [ep for ep in auth_endpoints_test if ep["requires_auth"] and ep["endpoint"] not in [r["endpoint"] for r in passing_endpoints]]
    if missing_auth:
        inconsistency_data.append({
            "ID": "AUTH-1",
            "Endpoint": "AUTH-ENDPOINTS",
            "Tipo": "Inconsistencia de Requisitos",
            "Detalle": f"{len(missing_auth)} endpoints auth que no requieren X-Admin-Key",
            "Criticidad": "ALTA"
        })

# Check for expected errors
if uploads_endpoint["status_code"] != "501":
    inconsistency_data.append({
        "ID": "UPLOADS-1",
        "Endpoint": f"/uploads",
        "Tipo": "Comportamiento Esperado",
        "Detalle": f"Expected 501 (Not Implemented), got {uploads_endpoint['status_code']}",
        "Criticidad": "MEDIA"
    })

table4 = generate_table(inconsistency_data, ["ID", "Endpoint", "Tipo", "Detalle", "Criticidad"])

with open("test_results_table4_inconsistencies.md", "w") as f:
    f.write("# Tabla 4: Inconsistencias\n\n")
    f.write("```markdown\n")
    f.write(table4)
    f.write("```\n")

print("✅ Tabla 4: Inconsistencias - Creada: test_results_table4_inconsistencies.md")
print()

# Resumen de resultados
summary = f"""
# 📊 RESUMEN DE TESTING

**Total de Endpoints Testeados:** {len(endpoints_list)}
- ✅ **PASARON:** {len(passing_endpoints)} ({len(passing_endpoints)/len(endpoints_list)*100:.1f}%)
- ❌ **FALLARON:** {len(failing_endpoints)} ({len(failing_endpoints)/len(endpoints_list)*100:.1f}%)
- ⚠️  **INCONSISTENCIAS:** {len(inconsistency_data)}

**Video ID de prueba usado:** {video_id}

**Archivos Generados:**
- test_results_table1_all_endpoints.md
- test_results_table2_passing.md
- test_results_table3_failing.md
- test_results_table4_inconsistencies.md
"""

with open("test_results_summary.md", "w") as f:
    f.write(summary)

print("✅ Resumen completado: test_results_summary.md")
print()

print("=" * 80)
print("🎉 TESTING COMPLETADO")
print("=" * 80)
print(summary)
print("=" * 80)
