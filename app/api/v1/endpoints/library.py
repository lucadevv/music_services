"""Library endpoints."""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

router = APIRouter(tags=["library"])


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Library information",
    description="Información sobre endpoints de biblioteca. Los endpoints de biblioteca requieren autenticación de usuario.",
    response_description="Información y endpoints públicos alternativos",
    responses={
        501: {
            "description": "Endpoint no implementado",
            "content": {
                "application/json": {
                    "example": {
                        "error": "NOT_IMPLEMENTED",
                        "message": "Library endpoints are not implemented in this version. Use /api/v1/explore for public content."
                    }
                }
            }
        }
    }
)
async def library_info() -> Dict[str, Any]:
    """
    Información sobre endpoints de biblioteca.
    
    Los endpoints de biblioteca requieren autenticación de usuario para acceder a contenido personal.
    Para contenido público, usa los endpoints de `/explore`, `/search` y `/browse`.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "NOT_IMPLEMENTED",
            "message": "Library endpoints are not implemented in this version. Use /api/v1/explore for public content."
        }
    )