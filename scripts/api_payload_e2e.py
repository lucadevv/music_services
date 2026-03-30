#!/usr/bin/env python3
"""
Smoke + payload check: HTTP status, metadata verification, and deprecation headers.
Run after: docker compose up (API on BASE_URL).
Env: MUSIC_API_KEY, ADMIN_SECRET_KEY (optional for admin-only checks).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
MUSIC_KEY = os.environ.get("MUSIC_API_KEY", "")
ADMIN_KEY = os.environ.get("ADMIN_SECRET_KEY", "")


def req(
    method: str,
    path: str,
    *,
    music_bearer: bool = True,
    admin: bool = False,
    body: Optional[dict] = None,
    timeout: int = 120,
) -> tuple[int, Any, dict[str, str]]:
    url = f"{BASE}{path}" if path.startswith("/") else f"{BASE}/{path}"
    headers: dict[str, str] = {}
    if music_bearer and MUSIC_KEY:
        headers["Authorization"] = f"Bearer {MUSIC_KEY}"
    if admin and ADMIN_KEY:
        headers["X-Admin-Key"] = ADMIN_KEY
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    response_headers: dict[str, str] = {}
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = resp.getcode()
            response_headers = dict(resp.headers)
    except urllib.error.HTTPError as e:
        code = e.code
        raw = e.read().decode("utf-8", errors="replace")
        if e.headers:
            response_headers = dict(e.headers)
    try:
        parsed = json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError:
        parsed = raw[:500]
    return code, parsed, response_headers


def check_metadata(name: str, payload: Any) -> list[str]:
    """Verify payload has meaningful metadata/fields populated."""
    issues = []
    if not isinstance(payload, dict):
        return [f"non-dict payload"]

    if payload.get("error") is True:
        return []

    required_fields_by_category = {
        "search": ["items", "query"],
        "browse home": ["items"],
        "browse song": ["videoDetails", "streamingData"],
        "browse related": ["items"],
        "explore root": ["moods_genres", "charts"],
        "explore moods list": ["categories"],
        "explore mood playlists": ["items"],
        "explore charts US": ["trending"],
        "watch": ["items"],
        "stream url": ["streamUrl", "title"],
        "podcast episodes playlist RDPN": [],
        "search suggestions": ["suggestions"],
        "admin auth/status": ["authenticated"],
        "admin stats/stats": ["service"],
        "admin api-keys list": ["total", "keys"],
        "admin stream cache stats": ["backend", "connected"],
        "browse album": ["title"],
        "browse artist albums": ["results"],
        "podcast channel": ["episodes"],
        "podcast channel episodes": ["episodes"],
    }

    required = required_fields_by_category.get(name, [])
    for field in required:
        if field not in payload:
            issues.append(f"missing field: {field}")
        elif payload[field] is None:
            issues.append(f"null field: {field}")
        elif isinstance(payload[field], (list, dict)) and not payload[field]:
            issues.append(f"empty field: {field}")

    return issues


def check_deprecated(name: str, headers: dict[str, str], expected_deprecated: bool = False) -> list[str]:
    """Check for deprecation headers."""
    issues = []
    warning = headers.get("Warning", "")
    deprecated = headers.get("X-Deprecated", "")

    if expected_deprecated:
        if not warning and not deprecated:
            issues.append("missing deprecation warning header")
        if warning and "299" not in warning:
            issues.append(f"wrong warning header: {warning}")

    return issues


def summarize_payload(name: str, code: int, payload: Any, headers: dict[str, str], metadata_issues: list[str] = None, deprecated_issues: list[str] = None) -> str:
    if metadata_issues is None:
        metadata_issues = []
    if deprecated_issues is None:
        deprecated_issues = []

    warnings = []

    if metadata_issues:
        warnings.append(f"META_FAIL({','.join(metadata_issues)})")
    if deprecated_issues:
        warnings.append(f"DEPRECATED({','.join(deprecated_issues)})")

    if isinstance(payload, dict) and payload.get("error") is True:
        return f"{name}: HTTP {code}  ERROR {payload.get('error_code')} — {payload.get('message', '')[:80]}"

    if not isinstance(payload, dict):
        preview = str(payload)[:120].replace("\n", " ")
        result = f"{name}: HTTP {code}  non-dict body: {preview}"
        if warnings:
            result += " | " + " ".join(warnings)
        return result

    keys = list(payload.keys())
    parts: list[str] = [f"HTTP {code}", f"keys={keys[:12]}{'…' if len(keys) > 12 else ''}"]

    if "items" in payload and isinstance(payload["items"], list):
        parts.append(f"items={len(payload['items'])}")
        if payload["items"]:
            fi = payload["items"][0]
            if isinstance(fi, dict):
                parts.append(f"first_item_keys={list(fi.keys())[:8]}")
    if "results" in payload and isinstance(payload["results"], list):
        parts.append(f"results={len(payload['results'])}")
    if "suggestions" in payload and isinstance(payload["suggestions"], list):
        parts.append(f"suggestions={len(payload['suggestions'])}")
    if "tracks" in payload and isinstance(payload["tracks"], list):
        parts.append(f"tracks={len(payload['tracks'])}")
    if "contents" in payload and isinstance(payload["contents"], list):
        parts.append(f"contents={len(payload['contents'])}")
    if "pagination" in payload and isinstance(payload["pagination"], dict):
        p = payload["pagination"]
        parts.append(f"pagination(total_results={p.get('total_results')},page={p.get('page')})")
    for ck in ("charts", "top_songs"):
        if ck in payload and isinstance(payload[ck], list):
            parts.append(f"{ck}={len(payload[ck])}")
            break
    if "trending" in payload and isinstance(payload["trending"], list):
        parts.append(f"trending={len(payload['trending'])}")
    if "categories" in payload and isinstance(payload["categories"], dict):
        parts.append(f"category_sections={len(payload['categories'])}")
    if "title" in payload and payload["title"]:
        parts.append(f"title={str(payload['title'])[:50]!r}")
    if "videoId" in payload and payload["videoId"]:
        parts.append(f"videoId={payload['videoId']!r}")
    if "episodes" in payload:
        ep = payload["episodes"]
        if isinstance(ep, list):
            parts.append(f"episodes(list)={len(ep)}")
        elif isinstance(ep, dict):
            r = ep.get("results")
            parts.append(f"episodes(dict keys={list(ep.keys())[:6]})")
            if isinstance(r, list):
                parts.append(f"episodes.results={len(r)}")

    result = f"{name}: " + " | ".join(parts)

    if warnings:
        result += " | " + " ".join(warnings)

    warning_header = headers.get("Warning", "")
    if warning_header:
        result += f" | Warning:{warning_header[:60]}"

    return result


def first_video_id(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    for item in payload.get("items") or []:
        if isinstance(item, dict):
            vid = item.get("videoId") or item.get("video_id")
            if vid:
                return str(vid)
    return None


def first_browse_album(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    for item in payload.get("items") or []:
        if isinstance(item, dict) and item.get("resultType") == "album":
            bid = item.get("browseId") or item.get("browse_id")
            if bid:
                return str(bid)
    return None


def main() -> int:
    if not MUSIC_KEY:
        print("Set MUSIC_API_KEY (Bearer for music routes).", file=sys.stderr)
        return 1

    lines: list[str] = []
    metadata_fails: list[str] = []
    deprecated_fails: list[str] = []

    def run(label: str, method: str, path: str, expected_deprecated: bool = False, **kwargs: Any) -> Any:
        code, payload, headers = req(method, path, **kwargs)

        meta_issues = check_metadata(label, payload)
        if meta_issues:
            metadata_fails.append(f"{label}: {', '.join(meta_issues)}")

        dep_issues = check_deprecated(label, headers, expected_deprecated)
        if dep_issues:
            deprecated_fails.append(f"{label}: {', '.join(dep_issues)}")

        lines.append(summarize_payload(label, code, payload, headers, meta_issues, dep_issues))
        return payload

    # ——— Admin (optional) ———
    if ADMIN_KEY:
        run("admin auth/status", "GET", "/auth/status", music_bearer=False, admin=True)
        run("admin stats/stats", "GET", "/stats/stats", music_bearer=False, admin=True)
        run("admin api-keys list", "GET", "/api-keys/", music_bearer=False, admin=True)
        run("admin stream cache stats", "GET", "/stream/cache/stats", music_bearer=False, admin=True)

    # ——— Discovery ———
    run("search", "GET", "/search/?q=cumbia&limit=5&page_size=5")
    _, search_mix, _ = req("GET", "/search/?q=cumbia&limit=10")
    vid = first_video_id(search_mix) if isinstance(search_mix, dict) else None

    _, search_albums, _ = req("GET", "/search/?q=cumbia&limit=15&filter=albums")
    album_id = (
        first_browse_album(search_albums) if isinstance(search_albums, dict) else None
    )

    playlist_id_search: Optional[str] = None
    _, search_pl, _ = req("GET", "/search/?q=cumbia&limit=5&filter=playlists")
    if isinstance(search_pl, dict):
        for it in search_pl.get("items") or []:
            if not isinstance(it, dict):
                continue
            playlist_id_search = it.get("playlistId") or it.get("playlist_id")
            if playlist_id_search:
                break

    run("browse home", "GET", "/browse/home?limit=3")

    artist_uc: Optional[str] = None
    if vid:
        run("browse song", "GET", f"/browse/song/{vid}")
        _, song_pl, _ = req("GET", f"/browse/song/{vid}")
        if isinstance(song_pl, dict):
            for a in song_pl.get("artists") or []:
                if not isinstance(a, dict):
                    continue
                aid = a.get("id") or a.get("browse_id") or a.get("channel_id")
                if aid and str(aid).startswith("UC"):
                    artist_uc = str(aid)
                    break
        run("browse related", "GET", f"/browse/song/{vid}/related")

    if album_id:
        run("browse album", "GET", f"/browse/album/{album_id}")

    run("explore root", "GET", "/explore/")
    run("explore moods list", "GET", "/explore/moods")
    mood_params: Optional[str] = None
    _, moods, _ = req("GET", "/explore/moods")
    cats = moods.get("categories") if isinstance(moods, dict) else None
    if isinstance(cats, dict):
        for section in cats.values():
            if isinstance(section, list) and section:
                for it in section:
                    if isinstance(it, dict) and it.get("params"):
                        mood_params = str(it["params"])
                        break
            if mood_params:
                break
    playlist_from_mood: Optional[str] = None
    if mood_params:
        run("explore mood playlists", "GET", f"/explore/moods/{mood_params}?page_size=3")
        _, mpl, _ = req("GET", f"/explore/moods/{mood_params}?page_size=5")
        if isinstance(mpl, dict):
            for it in mpl.get("items") or []:
                if not isinstance(it, dict):
                    continue
                playlist_from_mood = it.get("playlistId") or it.get("playlist_id")
                if not playlist_from_mood:
                    bid = it.get("browseId") or it.get("browse_id")
                    if isinstance(bid, str) and bid.startswith("VL"):
                        playlist_from_mood = bid[2:] if bid.startswith("VL") else bid
                    elif isinstance(bid, str):
                        playlist_from_mood = bid
                if playlist_from_mood:
                    break

    run("explore charts US", "GET", "/explore/charts?country=US")

    playlist_id: Optional[str] = None
    chart_vid: Optional[str] = None
    _, charts, _ = req("GET", "/explore/charts?country=US")
    if isinstance(charts, dict):
        for key in ("top_songs", "charts", "trending"):
            block = charts.get(key)
            if not isinstance(block, list):
                continue
            for it in block:
                if not isinstance(it, dict):
                    continue
                if not chart_vid:
                    chart_vid = it.get("videoId") or it.get("video_id")
                if not playlist_id:
                    pid = it.get("playlistId")
                    if isinstance(pid, str) and pid:
                        playlist_id = pid

    uc = artist_uc
    if not uc:
        _, art_search, _ = req("GET", "/search/?q=stanford%20podcast&limit=5&filter=artists")
        if isinstance(art_search, dict):
            for it in art_search.get("items") or []:
                if isinstance(it, dict):
                    bid = it.get("browseId") or it.get("browse_id")
                    if bid and str(bid).startswith("UC"):
                        uc = str(bid)
                        break

    if not playlist_id and playlist_from_mood:
        playlist_id = playlist_from_mood
    if not playlist_id and playlist_id_search:
        playlist_id = playlist_id_search

    use_vid = vid or chart_vid
    watch_playlist_id: Optional[str] = None
    if use_vid:
        run("watch", "GET", f"/watch?video_id={use_vid}&limit=5")
        _, wpl, _ = req("GET", f"/watch?video_id={use_vid}&limit=5")
        if isinstance(wpl, dict):
            watch_playlist_id = wpl.get("playlist_id")
        if not playlist_id and watch_playlist_id:
            playlist_id = watch_playlist_id
        if playlist_id:
            run("playlist", "GET", f"/playlists/{playlist_id}?limit=5")
        run("stream url", "GET", f"/stream/{use_vid}", timeout=180)

    if uc and str(uc).startswith("UC"):
        run("browse artist albums", "GET", f"/browse/artist/{uc}/albums?page_size=3")

    run("search suggestions", "GET", "/search/suggestions?q=cu")

    print("\n".join(lines))

    if metadata_fails:
        print("\n=== METADATA FAILURES ===", file=sys.stderr)
        for fail in metadata_fails:
            print(f"  - {fail}", file=sys.stderr)

    if deprecated_fails:
        print("\n=== DEPRECATION HEADER ISSUES ===", file=sys.stderr)
        for fail in deprecated_fails:
            print(f"  - {fail}", file=sys.stderr)

    fails = sum(1 for L in lines if "HTTP 500" in L or "HTTP 503" in L)
    warn_upstream = sum(1 for L in lines if "HTTP 502" in L)
    meta_fail_count = len(metadata_fails)
    dep_fail_count = len(deprecated_fails)

    print(
        f"\n--- summary: {len(lines)} checks, hard_failures={fails}, upstream_502={warn_upstream}, metadata_fails={meta_fail_count}, deprecation_issues={dep_fail_count}",
        file=sys.stderr,
    )

    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
