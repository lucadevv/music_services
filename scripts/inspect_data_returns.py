
import httpx
import json
import asyncio
from typing import Dict, Any, List, Optional

BASE_URL = "http://localhost:8000"
API_KEY = "sk_live_qlDNs3nImMnwj-rAXw2DTf9QiMLVEh1i"
ADMIN_KEY = "Aa123456."

# Headers
AUTH_HEADERS = {"Authorization": f"Bearer {API_KEY}"}
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_KEY}
ADMIN_FULL_HEADERS = {**AUTH_HEADERS, **ADMIN_HEADERS}

def print_response(name: str, response: httpx.Response):
    print(f"\n{'='*60}")
    print(f"DEBUG: {name}")
    print(f"Endpoint: {response.request.method} {response.request.url.path}")
    print(f"Status: {response.status_code}")
    
    try:
        data = response.json()
        # Truncate long lists or strings for readability
        if isinstance(data, dict):
            if "items" in data and isinstance(data["items"], list) and len(data["items"]) > 1:
                print(f"Data: {{'items': [1 of {len(data['items'])} items], ...}}")
                print(f"Sample Item: {json.dumps(data['items'][0], indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}...")
        else:
            print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}...")
    except Exception:
        print(f"Raw Content: {response.text[:500]}...")
    print(f"{'='*60}")

async def inspect_endpoints():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== INSPECCIÓN DE DATOS DE RETORNO ===\n")

        # 1. SEARCH (Para obtener IDs reales)
        print("Obteniendo IDs para pruebas...")
        search_res = await client.get(f"{BASE_URL}/api/v1/search/", headers=AUTH_HEADERS, params={"q": "Linkin Park", "limit": 1})
        video_id = None
        album_id = None
        artist_id = None
        
        if search_res.status_code == 200:
            items = search_res.json().get("items", [])
            for item in items:
                if not video_id and item.get("videoId"): video_id = item["videoId"]
                if not album_id and item.get("browseId") and "album" in (item.get("resultType") or ""): album_id = item["browseId"]
                if not artist_id and item.get("browseId") and "artist" in (item.get("resultType") or ""): artist_id = item["browseId"]

        # Si no se encontraron por tipo, forzar búsqueda específica
        if not artist_id:
            artist_search = await client.get(f"{BASE_URL}/api/v1/search/", headers=AUTH_HEADERS, params={"q": "Linkin Park", "filter": "artists", "limit": 1})
            if artist_search.status_code == 200:
                artist_items = artist_search.json().get("items", [])
                if artist_items: artist_id = artist_items[0].get("browseId")

        # 2. INSPECCIÓN
        # Public
        res = await client.get(f"{BASE_URL}/health")
        print_response("Health Check", res)

        # Search
        res = await client.get(f"{BASE_URL}/api/v1/search/", headers=AUTH_HEADERS, params={"q": "Numb", "limit": 2})
        print_response("Search Results", res)

        res = await client.get(f"{BASE_URL}/api/v1/search/suggestions", headers=AUTH_HEADERS, params={"q": "Linkin"})
        print_response("Search Suggestions", res)

        # Browse
        res = await client.get(f"{BASE_URL}/api/v1/browse/home", headers=AUTH_HEADERS, params={"limit": 1})
        print_response("Browse Home", res)

        if artist_id:
            res = await client.get(f"{BASE_URL}/api/v1/browse/artist/{artist_id}/albums", headers=AUTH_HEADERS)
            print_response("Artist Albums", res)

        if video_id:
            res = await client.get(f"{BASE_URL}/api/v1/browse/song/{video_id}", headers=AUTH_HEADERS)
            print_response("Song Metadata", res)
            
            res = await client.get(f"{BASE_URL}/api/v1/browse/lyrics-by-video/{video_id}", headers=AUTH_HEADERS)
            print_response("Lyrics", res)

        # Explore
        res = await client.get(f"{BASE_URL}/api/v1/explore/charts", headers=AUTH_HEADERS, params={"page_size": 1})
        print_response("Explore Charts", res)

        # Stream
        if video_id:
            res = await client.get(f"{BASE_URL}/api/v1/stream/{video_id}", headers=AUTH_HEADERS)
            print_response("Stream URL", res)

        # Admin
        res = await client.get(f"{BASE_URL}/api/v1/stats/stats", headers=ADMIN_HEADERS)
        print_response("Admin Stats", res)

        res = await client.get(f"{BASE_URL}/api/v1/auth/status", headers=ADMIN_HEADERS)
        print_response("Auth Status", res)

        print("\n=== INSPECCIÓN FINALIZADA ===")

if __name__ == "__main__":
    asyncio.run(inspect_endpoints())
