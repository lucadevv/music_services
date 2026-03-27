"""Schemas for OAuth authentication endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class CredentialsRequest(BaseModel):
    """Request body for saving OAuth credentials."""

    client_id: str = Field(
        ...,
        min_length=10,
        description="Google OAuth Client ID",
        examples=["188268615112-cdgjboq41lii1fdmbkl8ve2f96vqc059.apps.googleusercontent.com"],
    )
    client_secret: str = Field(
        ...,
        min_length=10,
        description="Google OAuth Client Secret",
        examples=["GOCSPX-xxxxxxxxxxxxxxxxx"],
    )


class CredentialsResponse(BaseModel):
    """Response for credential status."""

    has_credentials: bool = Field(
        ...,
        description="Whether OAuth credentials are stored",
    )
    updated_at: Optional[str] = Field(
        None,
        description="ISO timestamp of last credential update",
    )


class OAuthStartResponse(BaseModel):
    """Response for starting the OAuth device flow."""

    session_id: str = Field(
        ...,
        description="Session ID for polling",
    )
    verification_url: str = Field(
        ...,
        description="URL for user authorization",
        examples=["https://www.google.com/device"],
    )
    user_code: str = Field(
        ...,
        description="Code to enter at verification URL",
        examples=["XXXX-XXXX"],
    )
    expires_in: int = Field(
        ...,
        description="Seconds until session expires",
        examples=[900],
    )
    interval: int = Field(
        ...,
        description="Recommended polling interval in seconds",
        examples=[5],
    )


class OAuthPollRequest(BaseModel):
    """Request body for polling OAuth authorization."""

    session_id: str = Field(
        ...,
        min_length=1,
        description="Session ID from /auth/oauth/start",
    )


class OAuthPollPendingResponse(BaseModel):
    """Response when authorization is still pending."""

    status: str = Field(
        "pending",
        description="Authorization status",
    )
    message: str = Field(
        "Waiting for user authorization",
        description="Human-readable message",
    )


class OAuthPollAuthorizedResponse(BaseModel):
    """Response when authorization is complete."""

    status: str = Field(
        "authorized",
        description="Authorization status",
    )
    message: str = Field(
        "OAuth token saved successfully",
        description="Human-readable message",
    )


class AuthStatusResponse(BaseModel):
    """Response for authentication status check."""

    authenticated: bool = Field(
        ...,
        description="Whether the YTMusic client is authenticated",
    )
    has_credentials: bool = Field(
        ...,
        description="Whether OAuth credentials are stored in Redis",
    )
    has_token: bool = Field(
        ...,
        description="Whether oauth.json exists",
    )
    method: str = Field(
        "oauth",
        description="Authentication method",
    )
