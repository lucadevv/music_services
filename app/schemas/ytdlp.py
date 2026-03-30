"""Schemas for generic yt-dlp extraction."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class YtdlpRequest(BaseModel):
    """Request for generic yt-dlp extraction."""
    url: str = Field(..., description="URL del video o audio a extraer", examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    # download: bool = Field(False, description="Descargar el archivo (actualmente solo se soporta extracción)")

class YtdlpFormat(BaseModel):
    """A single format extracted by yt-dlp."""
    format_id: str = Field(..., alias="formatId", description="ID del formato")
    ext: str = Field(..., description="Extensión del archivo")
    resolution: Optional[str] = Field(None, description="Resolución")
    fps: Optional[float] = Field(None, description="Frames por segundo")
    acodec: Optional[str] = Field(None, description="Códec de audio")
    vcodec: Optional[str] = Field(None, description="Códec de video")
    url: str = Field(..., description="URL directa para este formato")
    filesize: Optional[int] = Field(None, description="Tamaño del archivo en bytes")

class YtdlpResponse(BaseModel):
    """Response for generic yt-dlp extraction."""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(..., description="ID del video/audio")
    title: str = Field(..., description="Título")
    description: Optional[str] = Field(None, description="Descripción")
    duration: Optional[int] = Field(None, description="Duración en segundos")
    uploader: Optional[str] = Field(None, description="Nombre del uploader")
    uploader_url: Optional[str] = Field(None, alias="uploaderUrl", description="URL del uploader")
    thumbnail: Optional[str] = Field(None, description="URL de la mejor miniatura")
    webpage_url: str = Field(..., alias="webpageUrl", description="URL original de la página")
    formats: List[YtdlpFormat] = Field(default_factory=list, description="Lista de formatos disponibles")
    best_audio_url: Optional[str] = Field(None, alias="bestAudioUrl", description="Mejor URL de solo audio encontrada")
    best_video_url: Optional[str] = Field(None, alias="bestVideoUrl", description="Mejor URL de video encontrada (con audio si está disponible)")
