from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from config.config import settings
from pipeline.interfaces import AudioGenerator
from pipeline.models import AudioItem as BaseAudioItem
from text_processor.context_analyzer import TextItem as AnalyzerTextItem

logger = logging.getLogger(__name__)


class AudioItem(BaseAudioItem):
    pass


class TextItem(AnalyzerTextItem):
    pass


class ElevenLabsTTS(AudioGenerator):
    """Generate speech via ElevenLabs if configured, else create a silent placeholder."""

    def __init__(self, voice_id: Optional[str] = None):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = voice_id or "Rachel"  # default public voice name/ID
        self.sample_rate = settings.audio_sample_rate
        self.format = settings.audio_format

    def run(self, item: TextItem) -> AudioItem:
        assert item.output_dir is not None, "TextItem.output_dir must be set by previous stage"
        audio_path = Path(item.output_dir) / f"speech.{self.format}"

        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not set. Creating a silent audio placeholder.")
            created_path = self._create_silent_audio(audio_path)
            return AudioItem(path=created_path)

        try:
            # Lazy import to avoid dependency if unused
            from elevenlabs import generate, set_api_key, save

            set_api_key(self.api_key)
            audio = generate(text=item.context_analysis.summary if item.context_analysis else item.content,
                             voice=self.voice_id)
            save(audio, str(audio_path))
        except Exception as e:
            logger.error(f"Failed to generate speech with ElevenLabs: {e}. Falling back to silent audio.")
            created_path = self._create_silent_audio(audio_path)
            audio_path = created_path

        return AudioItem(path=audio_path)

    def _create_silent_audio(self, audio_path: Path, duration_sec: int = 5) -> Path:
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from pydub import AudioSegment
            silent = AudioSegment.silent(duration=duration_sec * 1000, frame_rate=self.sample_rate)
            silent.export(str(audio_path), format=self.format)
            return audio_path
        except Exception as e:
            logger.error(f"Failed to create silent audio with pydub: {e}. Falling back to WAV via wave module.")
            try:
                import wave
                import struct
                n_channels = 1
                sampwidth = 2
                framerate = self.sample_rate
                n_frames = duration_sec * framerate
                wav_path = audio_path.with_suffix('.wav')
                with wave.open(str(wav_path), 'w') as wf:
                    wf.setnchannels(n_channels)
                    wf.setsampwidth(sampwidth)
                    wf.setframerate(framerate)
                    wf.writeframes(b"\x00\x00" * n_frames)
                if audio_path.suffix != '.wav':
                    try:
                        from pydub import AudioSegment as AS
                        AS.from_wav(str(wav_path)).export(str(audio_path), format=self.format)
                        return audio_path
                    except Exception:
                        return wav_path
            except Exception:
                audio_path.write_bytes(b"")
                return audio_path


