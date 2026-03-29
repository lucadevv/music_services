#!/bin/bash
set -e

echo "🚀 Starting YouTube Music Service..."

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z music_postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis
echo "⏳ Waiting for Redis..."
while ! nc -z music_redis 6379; do
  sleep 1
done
echo "✅ Redis is ready!"

# Initialize database
echo "🔧 Initializing database..."
python3 -c "
import asyncio
from app.core.database import init_db, create_admin_key_from_env

async def init():
    try:
        await init_db()
        print('✅ Database initialized')
        await create_admin_key_from_env()
        print('✅ Admin key initialized')
    except Exception as e:
        print(f'❌ Error initializing database: {e}')
        raise

asyncio.run(init())
"

# Execute main command
exec "$@"
