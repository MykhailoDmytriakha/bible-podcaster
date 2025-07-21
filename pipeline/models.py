"""Data models used across pipeline stages."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .base import PipelineItem


class TextItem(PipelineItem):
    """Represents a piece of text in the pipeline."""

    content: str = Field(..., description="Text content")


class AudioItem(PipelineItem):
    """Represents generated audio."""

    path: Path = Field(..., description="Path to audio file")


class ImageItem(PipelineItem):
    """Represents generated image."""

    path: Path = Field(..., description="Path to image file")


class VideoItem(PipelineItem):
    """Represents generated video."""

    path: Path = Field(..., description="Path to video file")
