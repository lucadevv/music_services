"""API Keys management system with Redis backend."""
import secrets
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.core.config import get_settings
settings = get_settings()
from app.core.cache_redis import get_redis_client
import logging

logger = logging.getLogger(__name__)

API_KEYS_PREFIX = "api_keys:"
MASTER_KEY_ID = "master"


class APIKey:
    """Represents a single API key."""
    
    def __init__(
        self,
        key_id: str,
        api_key: str,
        title: str,
        enabled: bool = True,
        created_at: Optional[str] = None,
        last_used: Optional[str] = None,
        is_master: bool = False,
    ):
        self.key_id = key_id
        self.api_key = api_key
        self.title = title
        self.enabled = enabled
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.last_used = last_used
        self.is_master = is_master
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "api_key": self.api_key,
            "title": self.title,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "is_master": self.is_master,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        """Create from dictionary."""
        return cls(
            key_id=data["key_id"],
            api_key=data["api_key"],
            title=data["title"],
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
            last_used=data.get("last_used"),
            is_master=data.get("is_master", False),
        )


class APIKeyManager:
    """Manages API keys with Redis backend."""
    
    def __init__(self):
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure master key exists."""
        if self._initialized:
            return
        
        if settings.ADMIN_SECRET_KEY:
            master = await self.get_by_id(MASTER_KEY_ID)
            if not master:
                await self.create_master_key(settings.ADMIN_SECRET_KEY)
                logger.info("Created master API key from ADMIN_SECRET_KEY")
        
        self._initialized = True
    
    async def create_master_key(self, secret: str) -> APIKey:
        """Create or update master API key."""
        master = APIKey(
            key_id=MASTER_KEY_ID,
            api_key=secret,
            title="Master Admin Key",
            enabled=True,
            is_master=True,
        )
        
        await self._save(master)
        logger.info("Master API key created/updated")
        return master
    
    async def create(
        self,
        title: str,
        api_key: Optional[str] = None,
    ) -> APIKey:
        """Create a new API key."""
        await self._ensure_initialized()
        
        key_id = secrets.token_urlsafe(8)
        api_key = api_key or f"sk_live_{secrets.token_urlsafe(32)}"
        
        api_key_obj = APIKey(
            key_id=key_id,
            api_key=api_key,
            title=title,
            enabled=True,
        )
        
        await self._save(api_key_obj)
        logger.info(f"Created API key: {key_id} - {title}")
        return api_key_obj
    
    async def get_by_key(self, api_key: str) -> Optional[APIKey]:
        """Get API key by the actual key value."""
        await self._ensure_initialized()
        
        try:
            client = await get_redis_client()
            keys = await client.keys(f"{API_KEYS_PREFIX}*")
            
            for key in keys:
                data = await client.get(key)
                if data:
                    api_key_obj = APIKey.from_dict(json.loads(data))
                    if api_key_obj.api_key == api_key:
                        return api_key_obj
            
            return None
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None
    
    async def get_by_id(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        try:
            client = await get_redis_client()
            data = await client.get(f"{API_KEYS_PREFIX}{key_id}")
            
            if data:
                return APIKey.from_dict(json.loads(data))
            return None
        except Exception as e:
            logger.error(f"Error getting API key by ID: {e}")
            return None
    
    async def list_all(self) -> List[APIKey]:
        """List all API keys."""
        await self._ensure_initialized()
        
        try:
            client = await get_redis_client()
            keys = await client.keys(f"{API_KEYS_PREFIX}*")
            
            api_keys = []
            for key in keys:
                data = await client.get(key)
                if data:
                    api_keys.append(APIKey.from_dict(json.loads(data)))
            
            return sorted(api_keys, key=lambda k: k.created_at, reverse=True)
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
    
    async def update(
        self,
        key_id: str,
        title: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[APIKey]:
        """Update an API key."""
        api_key = await self.get_by_id(key_id)
        
        if not api_key:
            return None
        
        if title is not None:
            api_key.title = title
        if enabled is not None:
            api_key.enabled = enabled
        
        await self._save(api_key)
        logger.info(f"Updated API key: {key_id}")
        return api_key
    
    async def delete(self, key_id: str) -> bool:
        """Delete an API key."""
        api_key = await self.get_by_id(key_id)
        
        if not api_key:
            return False
        
        if api_key.is_master:
            logger.warning("Cannot delete master API key")
            return False
        
        try:
            client = await get_redis_client()
            await client.delete(f"{API_KEYS_PREFIX}{key_id}")
            logger.info(f"Deleted API key: {key_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False
    
    async def verify(self, api_key: str) -> bool:
        """Verify if an API key is valid and enabled."""
        api_key_obj = await self.get_by_key(api_key)
        
        if not api_key_obj:
            return False
        
        if not api_key_obj.enabled:
            return False
        
        await self._update_last_used(api_key_obj.key_id)
        return True
    
    async def _save(self, api_key: APIKey):
        """Save API key to Redis."""
        try:
            client = await get_redis_client()
            await client.set(
                f"{API_KEYS_PREFIX}{api_key.key_id}",
                json.dumps(api_key.to_dict()),
            )
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            raise
    
    async def _update_last_used(self, key_id: str):
        """Update last used timestamp."""
        api_key = await self.get_by_id(key_id)
        if api_key:
            api_key.last_used = datetime.utcnow().isoformat()
            await self._save(api_key)


_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
