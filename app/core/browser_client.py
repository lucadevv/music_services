"""YouTube Music client with browser authentication and rotation."""
import asyncio
import json
import logging
import random
import time
import contextvars
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import HTTPException
from ytmusicapi import YTMusic
from app.core.config import get_settings

# Context variable to track the current account being used in the request
current_account_var = contextvars.ContextVar("current_account", default=None)

logger = logging.getLogger(__name__)

settings = get_settings()
BROWSER_ACCOUNTS_DIR = Path(settings.BROWSER_ACCOUNTS_DIR)
REDIS_RATE_LIMIT_KEY = "music:ratelimit:browser:"
REDIS_RATE_LIMIT_WINDOW = 300
REDIS_RATE_LIMIT_MAX = 10


class BrowserAccount:
    """Represents a single browser.json account."""
    
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.last_used = 0.0
        self.error_count = 0
        self.success_count = 0
        self.rate_limited_until = 0.0
        self.total_requests = 0
        # Semaphore to limit concurrent requests per account
        self.semaphore = asyncio.Semaphore(1) # Reduced to 1 for maximum stability
    
    def is_available(self) -> bool:
        """Check if this account can be used."""
        if time.time() < self.rate_limited_until:
            return False
        return True
    
    def mark_rate_limited(self, duration: int = 300):
        """Mark this account as rate limited."""
        self.rate_limited_until = time.time() + duration
        logger.warning(f"Account {self.name} rate limited for {duration}s")
    
    def mark_error(self):
        """Mark that this account had an error."""
        self.error_count += 1
        self.total_requests += 1
    
    def mark_success(self):
        """Mark that this account had a success."""
        self.success_count += 1
        self.total_requests += 1
        self.last_used = time.time()
        self.error_count = 0
    
    def clear_errors(self):
        """Clear error count after successful operations."""
        self.error_count = 0


class BrowserClientManager:
    """Manages multiple browser.json accounts with rotation."""
    
    def __init__(self):
        self.accounts: Dict[str, BrowserAccount] = {}
        self._scan_accounts()
    
    def _scan_accounts(self):
        """Scan for available browser.json files."""
        if not BROWSER_ACCOUNTS_DIR.exists():
            BROWSER_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created browser accounts directory: {BROWSER_ACCOUNTS_DIR}")
            return
        
        for path in BROWSER_ACCOUNTS_DIR.glob("*.json"):
            name = path.stem
            if name not in self.accounts:
                self.accounts[name] = BrowserAccount(path)
                logger.info(f"Found browser account: {name}")
    
    def get_all_accounts(self) -> List[BrowserAccount]:
        """Get all accounts regardless of availability."""
        return list(self.accounts.values())

    def get_available_accounts(self) -> List[BrowserAccount]:
        """Get list of available (not rate limited) accounts."""
        return [acc for acc in self.accounts.values() if acc.is_available()]
    
    def get_best_account(self) -> Optional[BrowserAccount]:
        """Get the best available account using round-robin with least-errors."""
        available = self.get_available_accounts()
        
        if not available:
            earliest = min(
                (acc for acc in self.accounts.values()),
                key=lambda a: a.rate_limited_until,
                default=None
            )
            if earliest:
                wait_time = earliest.rate_limited_until - time.time()
                logger.warning(
                    f"All accounts rate limited. Earliest available in {wait_time:.0f}s: {earliest.name}"
                )
            return None
        
        available.sort(key=lambda a: (a.error_count, a.last_used))
        return available[0]
    
    def register_rate_limit(self, account_name: str):
        """Register a rate limit error for an account."""
        if account_name in self.accounts:
            self.accounts[account_name].mark_rate_limited()
    
    def register_error(self, account_name: str):
        """Register an error for an account."""
        if account_name in self.accounts:
            self.accounts[account_name].mark_error()
    
    def register_success(self, account_name: str):
        """Register a successful operation for an account."""
        if account_name in self.accounts:
            self.accounts[account_name].mark_success()
    
    def add_account(self, name: str, headers: dict) -> str:
        """Add a new browser account from headers."""
        if not BROWSER_ACCOUNTS_DIR.exists():
            BROWSER_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
        
        safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        path = BROWSER_ACCOUNTS_DIR / f"{safe_name}.json"
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(headers, f, indent=2)
        
        self.accounts[safe_name] = BrowserAccount(path)
        logger.info(f"Added browser account: {safe_name}")
        
        return safe_name
    
    def remove_account(self, name: str) -> bool:
        """Remove a browser account."""
        if name in self.accounts:
            path = self.accounts[name].path
            if path.exists():
                path.unlink()
            del self.accounts[name]
            logger.info(f"Removed browser account: {name}")
            return True
        return False
    
    def list_accounts(self) -> List[dict]:
        """List all browser accounts with their status."""
        self._scan_accounts()
        # Sort by total_requests to see most used first
        sorted_accs = sorted(self.accounts.values(), key=lambda a: a.total_requests, reverse=True)
        return [
            {
                "name": acc.name,
                "available": acc.is_available(),
                "error_count": acc.error_count,
                "success_count": acc.success_count,
                "total_requests": acc.total_requests,
                "rate_limited_until": acc.rate_limited_until if not acc.is_available() else None,
                "last_used": acc.last_used,
            }
            for acc in sorted_accs
        ]


_browser_manager: Optional[BrowserClientManager] = None
_client_cache: Dict[str, YTMusic] = {}


def get_browser_manager() -> BrowserClientManager:
    """Get the global browser manager instance."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserClientManager()
    return _browser_manager


def _create_client(account: BrowserAccount) -> Optional[YTMusic]:
    """Create a YTMusic client from a browser account."""
    try:
        client = YTMusic(str(account.path))
        account.clear_errors()
        logger.info(f"Created YTMusic client for account: {account.name}")
        return client
    except Exception as e:
        logger.error(f"Failed to create client for {account.name}: {e}")
        account.mark_error()
        return None


def get_ytmusic() -> YTMusic:
    """Get YTMusic client with automatic rotation.
    
    Raises HTTPException 503 if no accounts are available.
    """
    manager = get_browser_manager()
    account = manager.get_best_account()
    
    if account is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": True,
                "error_code": "SERVICE_UNAVAILABLE",
                "message": (
                    "No hay cuentas de navegador disponibles. "
                    "Todas las cuentas están rate-limited. Esperá unos minutos e intentá de nuevo."
                ),
            },
        )
    
    # Register request in account metrics
    account.total_requests += 1
    
    # Store current account in context for error reporting
    current_account_var.set(account)
    
    cache_key = account.name
    if cache_key not in _client_cache:
        client = _create_client(account)
        if client is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": True,
                    "error_code": "SERVICE_UNAVAILABLE",
                    "message": f"No se pudo crear cliente para cuenta {account.name}",
                },
            )
        _client_cache[cache_key] = client
    
    return _client_cache[cache_key]


def get_ytmusic_with_account(account_name: str) -> YTMusic:
    """Get YTMusic client for a specific account."""
    manager = get_browser_manager()
    
    if account_name not in manager.accounts:
        raise HTTPException(
            status_code=404,
            detail=f"Cuenta {account_name} no encontrada",
        )
    
    account = manager.accounts[account_name]
    cache_key = f"specific_{account_name}"
    
    if cache_key not in _client_cache:
        client = _create_client(account)
        if client is None:
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo crear cliente para cuenta {account_name}",
            )
        _client_cache[cache_key] = client
    
    return _client_cache[cache_key]


def reset_client_cache():
    """Clear the client cache to force re-creation."""
    global _client_cache
    _client_cache = {}


def is_authenticated() -> bool:
    """Check if at least one browser account is available."""
    manager = get_browser_manager()
    return len(manager.get_available_accounts()) > 0


def get_auth_status() -> dict:
    """Get authentication status."""
    manager = get_browser_manager()
    accounts = manager.list_accounts()
    available = manager.get_available_accounts()
    
    # Calculate usage metrics
    total_reqs = sum(acc.get("total_requests", 0) for acc in accounts)
    
    return {
        "authenticated": len(available) > 0,
        "total_accounts": len(accounts),
        "available_accounts": len(available),
        "total_requests_all_accounts": total_reqs,
        "accounts": accounts,
        "method": "browser",
    }
