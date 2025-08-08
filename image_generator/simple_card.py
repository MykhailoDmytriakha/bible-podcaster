from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from config.config import settings
from pipeline.interfaces import ImageGenerator
from pipeline.models import ImageItem as BaseImageItem
from text_processor.context_analyzer import TextItem as AnalyzerTextItem

logger = logging.getLogger(__name__)


class ImageItem(BaseImageItem):
    pass


class TextItem(AnalyzerTextItem):
    pass


class SimpleCardGenerator(ImageGenerator):
    """Create a simple typographic card with the topic and summary."""

    def __init__(self):
        self.width = settings.image_width
        self.height = settings.image_height
        self.format = settings.image_format

    def run(self, item: TextItem) -> ImageItem:
        assert item.output_dir is not None, "TextItem.output_dir must be set by previous stage"
        image_path = Path(item.output_dir) / f"cover.{self.format}"

        title = (item.context_analysis.topic if item.context_analysis else "Bible Podcaster")
        subtitle = (item.context_analysis.summary if item.context_analysis else item.content)
        if len(subtitle) > 220:
            subtitle = subtitle[:217] + "..."

        img = Image.new("RGB", (self.width, self.height), color=(18, 18, 18))
        draw = ImageDraw.Draw(img)

        # Try to load a reasonable default font
        try:
            font_title = ImageFont.truetype("Arial.ttf", 72)
            font_sub = ImageFont.truetype("Arial.ttf", 36)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        # Calculate positions
        margin = 80
        y = margin
        draw.text((margin, y), title, font=font_title, fill=(240, 240, 240))
        y += 120

        # Wrap subtitle text
        wrapped = self._wrap_text(subtitle, draw, font_sub, self.width - margin * 2)
        draw.multiline_text((margin, y), wrapped, font=font_sub, fill=(200, 200, 200), spacing=8)

        image_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(image_path))
        return ImageItem(path=image_path)

    def _wrap_text(self, text: str, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, max_width: int) -> str:
        words = text.split()
        lines: list[str] = []
        current_words: list[str] = []
        for word in words:
            tentative = " ".join(current_words + [word])
            bbox = draw.textbbox((0, 0), tentative, font=font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_words.append(word)
            else:
                if current_words:
                    lines.append(" ".join(current_words))
                current_words = [word]
        if current_words:
            lines.append(" ".join(current_words))
        return "\n".join(lines)


