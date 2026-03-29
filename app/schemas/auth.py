"""Schemas for browser authentication endpoints."""
from typing import Optional, List
from pydantic import BaseModel, Field


class BrowserAddResponse(BaseModel):
    """Response when adding a browser account."""

    success: bool = Field(..., description="Whether the account was added successfully")
    account_name: str = Field(..., description="Name of the added account")
    message: str = Field(..., description="Human-readable message")


class BrowserAccountInfo(BaseModel):
    """Information about a browser account."""

    name: str = Field(..., description="Account name")
    available: bool = Field(..., description="Whether the account is available")
    error_count: int = Field(..., description="Number of consecutive errors")
    rate_limited_until: Optional[float] = Field(None, description="Unix timestamp when rate limit expires")
    last_used: float = Field(..., description="Unix timestamp of last use")


class BrowserListResponse(BaseModel):
    """Response listing all browser accounts."""

    total: int = Field(..., description="Total number of accounts")
    available: int = Field(..., description="Number of available accounts")
    accounts: List[BrowserAccountInfo] = Field(..., description="List of accounts")


class BrowserTestResponse(BaseModel):
    """Response for authentication test."""

    success: bool = Field(..., description="Whether authentication works")
    message: str = Field(..., description="Human-readable message")
    account_used: Optional[str] = Field(None, description="Account used for the test")


class AuthStatusResponse(BaseModel):
    """Response for authentication status check."""

    authenticated: bool = Field(..., description="Whether the service is authenticated")
    method: str = Field(..., description="Authentication method (browser)")
    total_accounts: int = Field(..., description="Total number of accounts")
    available_accounts: int = Field(..., description="Number of available accounts")
    accounts: List[BrowserAccountInfo] = Field(default_factory=list, description="List of accounts")
