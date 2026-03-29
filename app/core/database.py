"""Database configuration and connection management."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.core.config import get_settings

settings = get_settings()

DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=50,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db():
    """Initialize database and create tables."""
    async with engine.begin() as conn:
        await conn.run(text("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                key_id VARCHAR(50) UNIQUE NOT NULL,
                api_key VARCHAR(100) UNIQUE NOT NULL,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT true,
                is_admin BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
            CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id);
        """))
    print("✅ Database initialized successfully")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_admin_key_from_env():
    """Create admin API key from ADMIN_SECRET_KEY environment variable."""
    from app.core.config import get_settings
    from datetime import datetime
    
    settings = get_settings()
    
    if not settings.ADMIN_SECRET_KEY:
        print("⚠️  WARNING: ADMIN_SECRET_KEY not set in environment")
        return
    
    async with AsyncSessionLocal() as session:
        # Check if admin key already exists
        result = await session.execute(
            text("SELECT key_id FROM api_keys WHERE is_admin = true")
        )
        existing_admin = result.fetchone()
        
        if not existing_admin:
            # Generate admin key from ADMIN_SECRET_KEY
            admin_key = f"sk_admin_{settings.ADMIN_SECRET_KEY[:16]}"
            
            await session.execute(
                text("""
                    INSERT INTO api_keys (key_id, api_key, title, description, enabled, is_admin)
                    VALUES (:key_id, :api_key, :title, :description, true, true)
                """),
                {
                    "key_id": "admin",
                    "api_key": admin_key,
                    "title": "Super Admin",
                    "description": "Auto-generated from ADMIN_SECRET_KEY"
                }
            )
            await session.commit()
            print(f"")
            print(f"🔐 MASTER API KEY CREATED:")
            print(f"   {admin_key}")
            print(f"")
            print(f"⚠️  SAVE this key securely! It will not be shown again.")
            print(f"")
        else:
            print("✅ Admin API key already exists in database")