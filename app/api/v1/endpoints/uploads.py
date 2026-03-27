"""Upload endpoints."""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

router = APIRouter(tags=["uploads"])


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Uploads information",
    description="Información sobre endpoints de uploads. Los endpoints de uploads requieren autenticación de usuario.",
    response_description="Información y endpoints públicos alternativos",
    responses={
        501: {
            "description": "Endpoint no implementado",
            "content": {
                "application/json": {
                    "example": {
                        "error": "NOT_IMPLEMENTED",
                        "message": "Upload endpoints are not implemented in this version. Use /api/v1/explore for public content."
                    }
                }
            }
        }
    }
)
async def uploads_info() -> Dict[str, Any]:
    """
    Información sobre endpoints de uploads.
    
    Los endpoints de uploads requieren autenticación de usuario para gestionar contenido personal subido.
    Para contenido público, usa los endpoints de `/explore`, `/search` y `/browse`.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "NOT_IMPLEMENTED",
            "message": "Upload endpoints are not implemented in this version. Use /api/v1/explore for public content."
        }
    )