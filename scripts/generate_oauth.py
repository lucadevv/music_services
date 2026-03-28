#!/usr/bin/env python3
"""
Generate oauth.json for ytmusicapi using OAuth Device Flow.

This script works around a known bug in ytmusicapi 1.10.3 where Google
returns a 'refresh_token_expires_in' field that causes a TypeError.

Usage:
    python scripts/generate_oauth.py

It reads YTMUSIC_CLIENT_ID and YTMUSIC_CLIENT_SECRET from .env or environment.
"""
import json
import os
import sys
import time
from pathlib import Path

try:
    from httpx import post
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)


GOOGLE_DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def load_env():
    """Load variables from .env file if present."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def get_credentials():
    """Get client_id and client_secret from environment."""
    client_id = os.environ.get("YTMUSIC_CLIENT_ID", "")
    client_secret = os.environ.get("YTMUSIC_CLIENT_SECRET", "")
    return client_id, client_secret


def start_device_flow(client_id: str, client_secret: str) -> dict:
    """Start OAuth Device Flow — returns device_code, user_code, verification_url."""
    resp = post(GOOGLE_DEVICE_CODE_URL, data={
        "client_id": client_id,
        "scope": "https://www.googleapis.com/auth/youtube",
    })
    if resp.status_code != 200:
        print(f"Error starting device flow: {resp.status_code} {resp.text}")
        sys.exit(1)
    return resp.json()


def poll_for_token(client_id: str, client_secret: str, device_code: str, interval: int = 5) -> dict:
    """Poll Google until user authorizes the app."""
    print("Esperando autorización...")
    while True:
        time.sleep(interval)
        resp = post(GOOGLE_TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        data = resp.json()

        if "access_token" in data:
            return data

        error = data.get("error")
        if error == "authorization_pending":
            continue
        elif error == "slow_down":
            interval += 5
        elif error == "expired_token":
            print("El código expiró. Ejecutá el script de nuevo.")
            sys.exit(1)
        elif error == "access_denied":
            print("Acceso denegado por el usuario.")
            sys.exit(1)
        else:
            print(f"Error: {error} — {data.get('error_description', '')}")
            sys.exit(1)


def main():
    load_env()
    client_id, client_secret = get_credentials()

    if not client_id or not client_secret:
        print("Error: YTMUSIC_CLIENT_ID y YTMUSIC_CLIENT_SECRET deben estar configurados.")
        print("Configuralos en .env o como variables de entorno.")
        sys.exit(1)

    print(f"Client ID: {client_id[:20]}...\n")

    # Step 1: Start device flow
    device_data = start_device_flow(client_id, client_secret)
    verification_url = device_data["verification_url"]
    user_code = device_data["user_code"]
    interval = device_data.get("interval", 5)
    device_code = device_data["device_code"]

    print(f"1. Abrí en tu browser: {verification_url}")
    print(f"2. Ingresá este código: {user_code}")
    print(f"3. Autorizá la aplicación\n")

    # Step 2: Poll for token
    token_data = poll_for_token(client_id, client_secret, device_code, interval)

    # Step 3: Build oauth.json (filter out refresh_token_expires_in — ytmusicapi 1.10.3 bug)
    oauth_data = {
        "access_token": token_data["access_token"],
        "expires_in": token_data["expires_in"],
        "scope": token_data["scope"],
        "token_type": token_data["token_type"],
        "refresh_token": token_data["refresh_token"],
        "expires_at": int(time.time()) + token_data["expires_in"],
    }

    output_path = Path(__file__).parent.parent / "oauth.json"
    output_path.write_text(json.dumps(oauth_data, indent=2))
    print(f"\n✅ oauth.json generado en: {output_path}")


if __name__ == "__main__":
    main()
