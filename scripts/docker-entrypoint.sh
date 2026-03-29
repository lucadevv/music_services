#!/bin/bash
set -e

echo "🚀 Iniciando YouTube Music Service..."

BROWSER_DIR="/app/browser"
mkdir -p "$BROWSER_DIR"
chmod -R 777 "$BROWSER_DIR" 2>/dev/null || true

if [ -z "$ADMIN_SECRET_KEY" ]; then
    echo "⚠️  WARNING: ADMIN_SECRET_KEY no está configurado"
    echo "   Configuralo en .env para mayor seguridad"
fi

if [ "$1" = "uvicorn" ]; then
    echo "🔧 Inicializando API keys..."
    
    python3 -c "
import asyncio
import sys
from app.core.api_keys import get_api_key_manager

async def init_master_key():
    try:
        manager = get_api_key_manager()
        keys = await manager.list_all()
        
        if not keys:
            print('⚠️  No API keys found. Creating master API key...')
            master_key = await manager.create_master_key()
            print(f'')
            print(f'🔐 MASTER API KEY CREATED:')
            print(f'   {master_key.api_key}')
            print(f'')
            print(f'⚠️  SAVE THIS KEY SECURELY! It will not be shown again.')
            print(f'')
        else:
            master_exists = any(k.is_master for k in keys)
            if not master_exists:
                print('⚠️  No master API key found. Creating one...')
                master_key = await manager.create_master_key()
                print(f'')
                print(f'🔐 MASTER API KEY CREATED:')
                print(f'   {master_key.api_key}')
                print(f'')
                print(f'⚠️  SAVE THIS KEY SECURELY! It will not be shown again.')
                print(f'')
            else:
                print(f'✅ API keys already initialized')
    except Exception as e:
        print(f'❌ Error initializing API keys: {e}')
        sys.exit(1)

asyncio.run(init_master_key())
" || echo "⚠️  Could not initialize API keys (Redis not ready?)"
    
    echo "🚀 Starting YouTube Music Service..."
fi

exec "$@"
