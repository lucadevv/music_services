"""Documentation-focused auth dependencies for endpoint docs."""
from fastapi import Header, HTTPException


async def require_music_bearer_header(
    authorization: str = Header(
        ...,
        alias="Authorization",
        description="Music API key header. Format: Bearer <api_key>",
    ),
) -> None:
    """Declare Authorization header in OpenAPI for music endpoints."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Use 'Authorization: Bearer <api_key>' format",
        )
