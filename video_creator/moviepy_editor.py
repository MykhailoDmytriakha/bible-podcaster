from __future__ import annotations

import logging
from pathlib import Path

from pipeline.interfaces import VideoCreator
from pipeline.models import VideoItem as BaseVideoItem
from audio_generator.elevenlabs_tts import AudioItem
from image_generator.simple_card import ImageItem
from config.config import settings

logger = logging.getLogger(__name__)


class VideoItem(BaseVideoItem):
    pass


class SimpleVideoCreator(VideoCreator):
    """Combine audio and image into a simple MP4 video with fades."""

    def __init__(self):
        self.fps = settings.video_fps
        self.format = settings.video_format

    def run(self, item: tuple[AudioItem, ImageItem]) -> VideoItem:
        audio_item, image_item = item
        output_dir = image_item.path.parent
        video_path = Path(output_dir) / f"video.{self.format}"

        try:
            # Lazy import; support both moviepy v1 (editor submodule) and v2 (top-level)
            try:
                from moviepy import ImageClip, AudioFileClip  # moviepy>=2
            except Exception:
                from moviepy.editor import ImageClip, AudioFileClip  # moviepy<2

            duration = self._get_audio_duration(audio_item)
            try:
                image_clip = ImageClip(str(image_item.path)).with_duration(duration)  # moviepy>=2
            except Exception:
                image_clip = ImageClip(str(image_item.path)).set_duration(duration)  # moviepy<2

            # Try to attach audio; fall back to silent video
            try:
                audio_clip = AudioFileClip(str(audio_item.path))
                try:
                    image_clip = image_clip.with_audio(audio_clip)  # moviepy>=2
                except Exception:
                    image_clip = image_clip.set_audio(audio_clip)  # moviepy<2
            except Exception:
                logger.warning("Audio not available; creating video without audio track.")

            # Simple fades
            try:
                image_clip = image_clip.fadein(0.5).fadeout(0.5)
            except Exception:
                pass
            image_clip.write_videofile(
                str(video_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_dir / "temp-audio.m4a"),
                remove_temp=True,
                threads=2,
            )
        except Exception as e:
            logger.error(f"Failed to create video with moviepy: {e}")
            raise

        return VideoItem(path=video_path)

    def _get_audio_duration(self, audio_item: AudioItem) -> float:
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_item.path))
            return max(1.0, audio.duration_seconds)
        except Exception:
            return 5.0


