#!/bin/bash
set -e

OAUTH_DIR="/app/oauth"
OAUTH_FILE="${OAUTH_DIR}/oauth.json"

mkdir -p "$OAUTH_DIR"
chmod -R 777 "$OAUTH_DIR" 2>/dev/null || true

touch "$OAUTH_FILE" 2>/dev/null || true
chmod 666 "$OAUTH_FILE" 2>/dev/null || true

if [ ! -s "$OAUTH_FILE" ]; then
    echo '{}' > "$OAUTH_FILE" 2>/dev/null || true
    if [ -s "$OAUTH_FILE" ]; then
        echo "[entrypoint] Created empty oauth.json"
    else
        echo "[entrypoint] Will create on first OAuth"
    fi
else
    echo "[entrypoint] oauth.json already exists"
fi

exec "$@"
