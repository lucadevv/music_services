#!/bin/bash
set -e

echo "🚀 Starting YouTube Music Service..."

# Wait for PostgreSQL
echo "⏳  Waiting for PostgreSQL..."
sleep 5

# Initialize database
python3 -c "
import asyncio
from app.core.database import init_db, create_admin_key_from_env

async def init():
    await init_db()
    await create_admin_key_from_env()
    print('✅ Database initialized')

asyncio.run(init())

# Execute main command
exec "$@"
