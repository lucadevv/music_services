
import httpx
import json
import asyncio
import sys
from typing import Dict, Any, List, Optional

BASE_URL = "http://localhost:8000"
API_KEY = "sk_live_qlDNs3nImMnwj-rAXw2DTf9QiMLVEh1i"
ADMIN_KEY = "Aa123456."

# Headers
AUTH_HEADERS = {"Authorization": f"Bearer {API_KEY}"}
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_KEY}
# For endpoints requiring both
FULL_AUTH_HEADERS = {**AUTH_HEADERS, **ADMIN_HEADERS}

async def call(name: str, method: str, path: str, headers: dict = None, params: dict = None, json_body: dict = None):
    url = f"{BASE_URL}{path}"
    print(f"\n🚀 TESTING: {name} ({method} {path})")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(method, url, headers=headers, params=params, json=json_body)
            print(f"STATUS: {response.status_code}")
            try:
                data = response.json()
                # Print full data but truncate very long lists for terminal sanity
                if isinstance(data, dict) and "items" in data and len(data["items"]) > 5:
                    print(f"DATA (Truncated items list): {json.dumps({**data, 'items': data['items'][:2] + ['... (more)']}, indent=2, ensure_ascii=False)}")
                else:
                    print(f"DATA: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return response, data
            except:
                print(f"RAW: {response.text[:500]}")
                return response, response.text
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None, str(e)

async def run_full_test():
    print("=== STARTING COMPREHENSIVE API INSPECTION ===\n")

    # 1. PUBLIC
    await call("Health Check", "GET", "/health")

    # 2. API KEYS (Admin)
    _, create_res = await call("Create API Key", "POST", "/api/v1/api-keys/", headers=ADMIN_HEADERS, json_body={"title": "Test Key", "description": "For inspection"})
    test_key_id = create_res.get("key_id") if isinstance(create_res, dict) else None
    
    await call("List API Keys", "GET", "/api/v1/api-keys/", headers=ADMIN_HEADERS)
    
    if test_key_id:
        await call("Get API Key", "GET", f"/api/v1/api-keys/{test_key_id}", headers=ADMIN_HEADERS)
        await call("Update API Key", "PATCH", f"/api/v1/api-keys/{test_key_id}", headers=ADMIN_HEADERS, json_body={"title": "Updated Test Key"})
        await call("Delete API Key", "DELETE", f"/api/v1/api-keys/{test_key_id}", headers=ADMIN_HEADERS)

    # 3. AUTH (Admin)
    await call("Auth Status", "GET", "/api/v1/auth/status", headers=ADMIN_HEADERS)
    await call("List Browser Accounts", "GET", "/api/v1/auth/browser", headers=ADMIN_HEADERS)
    await call("Test Browser Auth", "POST", "/api/v1/auth/browser/test", headers=ADMIN_HEADERS)

    # 4. SEARCH (API Key)
    _, search_res = await call("Search Music", "GET", "/api/v1/search/", headers=AUTH_HEADERS, params={"q": "Linkin Park", "limit": 2})
    
    video_id = "BLZWkjBXfN8" # Fallback
    album_id = "MPREb_qMlbe7gLeuH" # Fallback
    artist_id = "UCxgN32UVVztKAQd2HkXzBtw" # Fallback
    
    if isinstance(search_res, dict) and search_res.get("items"):
        for item in search_res["items"]:
            if not video_id and item.get("videoId"): video_id = item["videoId"]
            if not album_id and item.get("browseId") and "album" in str(item.get("resultType", "")): album_id = item["browseId"]
            if not artist_id and item.get("browseId") and "artist" in str(item.get("resultType", "")): artist_id = item["browseId"]

    await call("Search Suggestions", "GET", "/api/v1/search/suggestions", headers=AUTH_HEADERS, params={"q": "Linkin"})

    # 5. BROWSE (API Key)
    await call("Browse Home", "GET", "/api/v1/browse/home", headers=AUTH_HEADERS, params={"limit": 1})
    if artist_id:
        await call("Artist Albums", "GET", f"/api/v1/browse/artist/{artist_id}/albums", headers=AUTH_HEADERS)
    if album_id:
        await call("Album Info", "GET", f"/api/v1/browse/album/{album_id}", headers=AUTH_HEADERS, params={"page_size": 2})
        await call("Album Browse ID", "GET", f"/api/v1/browse/album/{album_id}/browse-id", headers=AUTH_HEADERS)
    if video_id:
        await call("Song Metadata", "GET", f"/api/v1/browse/song/{video_id}", headers=AUTH_HEADERS)
        await call("Related Songs", "GET", f"/api/v1/browse/song/{video_id}/related", headers=AUTH_HEADERS, params={"page_size": 2})
        await call("Lyrics by Video", "GET", f"/api/v1/browse/lyrics-by-video/{video_id}", headers=AUTH_HEADERS)

    # 6. EXPLORE (API Key)
    _, explore_res = await call("Explore Root", "GET", "/api/v1/explore/", headers=AUTH_HEADERS)
    mood_params = None
    if isinstance(explore_res, dict) and explore_res.get("moods_genres"):
        mood_params = explore_res["moods_genres"][0].get("params")

    await call("Mood Categories", "GET", "/api/v1/explore/moods", headers=AUTH_HEADERS)
    if mood_params:
        await call("Mood Playlists", "GET", f"/api/v1/explore/moods/{mood_params}", headers=AUTH_HEADERS, params={"page_size": 2})
    await call("Explore Charts", "GET", "/api/v1/explore/charts", headers=AUTH_HEADERS, params={"page_size": 2})

    # 7. PLAYLISTS (API Key)
    playlist_id = "PLOLAK5uy_kOhykI48RrrotDGkUMSgHmg_i0LI_TNgU" # Example
    await call("Get Playlist", "GET", f"/api/v1/playlists/{playlist_id}", headers=AUTH_HEADERS, params={"page_size": 2})

    # 8. WATCH (API Key)
    if video_id:
        await call("Get Watch Playlist", "GET", "/api/v1/watch/", headers=AUTH_HEADERS, params={"video_id": video_id, "limit": 5})

    # 9. STREAM (API Key + Admin)
    if video_id:
        await call("Get Stream URL", "GET", f"/api/v1/stream/{video_id}", headers=AUTH_HEADERS)
        await call("Stream Batch", "GET", "/api/v1/stream/batch", headers=AUTH_HEADERS, params={"ids": f"{video_id},kXYiU_JCYtU"})
        await call("Stream Cache Stats", "GET", "/api/v1/stream/cache/stats", headers=FULL_AUTH_HEADERS)
        await call("Stream Cache Info", "GET", f"/api/v1/stream/cache/info/{video_id}", headers=FULL_AUTH_HEADERS)
        await call("Stream Status", "GET", f"/api/v1/stream/status/{video_id}", headers=FULL_AUTH_HEADERS)

    # 10. STATS (Admin)
    await call("Service Stats", "GET", "/api/v1/stats/stats", headers=ADMIN_HEADERS)

    print("\n=== INSPECTION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_full_test())
