"""Interfaces for common pipeline stages."""
from __future__ import annotations

import abc

from .base import PipelineStage
from .models import TextItem, AudioItem, ImageItem, VideoItem


class TextProcessor(PipelineStage):
    """Interface for text processing stage."""

    @abc.abstractmethod
    def run(self, item: TextItem) -> TextItem:
        """Process raw text and return processed text."""
        pass


class AudioGenerator(PipelineStage):
    """Interface for audio generation stage."""

    @abc.abstractmethod
    def run(self, item: TextItem) -> AudioItem:
        """Generate audio from processed text."""
        pass


class ImageGenerator(PipelineStage):
    """Interface for image generation stage."""

    @abc.abstractmethod
    def run(self, item: TextItem) -> ImageItem:
        """Create an image based on processed text."""
        pass


class VideoCreator(PipelineStage):
    """Interface for video creation stage."""

    @abc.abstractmethod
    def run(self, item: tuple[AudioItem, ImageItem]) -> VideoItem:
        """Combine audio and image into a video."""
        pass


class Uploader(PipelineStage):
    """Interface for uploading stage."""

    @abc.abstractmethod
    def run(self, item: VideoItem) -> VideoItem:
        """Upload video to destination platform."""
        pass
