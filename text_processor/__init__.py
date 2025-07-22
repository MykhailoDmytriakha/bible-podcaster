from pathlib import Path
from datetime import datetime
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from config.config import settings
from pipeline.interfaces import TextProcessor
from pipeline.models import TextItem as BaseTextItem

logger = logging.getLogger(__name__)

class ContextAnalysisResult(BaseModel):
    topic: str = Field(..., description="2-5 word topic for folder name on English")
    bible_references: List[str] = Field(..., description="List of Bible references mentioned in the text, like 'John 3:16', 'Genesis 1:1', 'Psalm 23:1'")
    keywords: List[str] = Field(..., description="List of keywords from the text")

# Расширяем TextItem для поддержки context_analysis
class TextItem(BaseTextItem):
    context_analysis: Optional[ContextAnalysisResult] = None

class BiblicalContextAnalyzer(TextProcessor):
    """Pipeline step: analyzes biblical context, extracts topic, references, keywords."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = getattr(settings, 'openai_model', 'o4-mini')
        self.output_dir = settings.get_absolute_path(settings.output_dir)

    def run(self, item: TextItem) -> TextItem:
        prompt = (
            "Extract topic (2-5 words, for folder name), all Bible references, and keywords from the text. "
            "Return only the structured data."
            "Language: English"
            " - for topic use only English words"
            " - for bible references use base on user language"
            " - for keywords use base on user language"
        )
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": item.content},
            ],
            text_format=ContextAnalysisResult,
        )
        result = response.output_parsed
        if result is None:
            logger.error("OpenAI did not return a valid structured result.")
            raise ValueError("No structured result from OpenAI")

        # 2. Create output folder
        today = datetime.now().strftime("%Y%m%d")
        topic_folder = f"{today}_{result.topic.replace(' ', '')[:32]}"
        folder_path = self.output_dir / topic_folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # 3. Save input and result
        input_path = folder_path / "input.txt"
        result_path = folder_path / "context_analysis.json"
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(item.content)
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        # 4. Attach result to item for downstream pipeline
        item.context_analysis = result
        return item
