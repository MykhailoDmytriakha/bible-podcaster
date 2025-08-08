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


class BibleReference(BaseModel):
    """Structured bible reference with quotes and context."""
    reference: str = Field(..., description="Bible reference like 'Genesis 1:1-31', 'Joshua 6:1-20'")
    quotes: List[str] = Field(..., description="Biblical quotes in user's language, each at least one sentence, may use ellipsis (...) for long passages")
    context: str = Field(..., description="Brief explanation of what this verse/passage is about (context of the verse, not user text)")

class ContextEvaluation(BaseModel):
    """Context evaluation result."""
    is_context_sufficient: bool = Field(..., description="Whether the context is sufficient for podcast creation")
    missing_elements: List[str] = Field(default=[], description="List of missing elements that need enrichment")
    enrichment_suggestions: List[str] = Field(default=[], description="Suggestions for what to add/enrich")
    completeness_score: float = Field(..., description="Completeness score from 0.0 to 1.0")
    thought_completeness: str = Field(..., description="Assessment of thought completeness: 'complete', 'partial', 'incomplete'")


class ContextAnalysisResult(BaseModel):
    """Enhanced biblical context analysis result."""
    topic: str = Field(..., description="2-5 word topic for folder name in English")
    bible_references: List[BibleReference] = Field(default=[], description="List of biblical references with quotes and context")
    keywords: List[str] = Field(..., description="List of keywords from the text in user's language")
    themes: List[str] = Field(default=[], description="Theological, psychological, historical themes if present")
    structure: Optional[str] = Field(None, description="Description of thought structure if present (repetition, climax, rhythm, logic)")
    typologies_and_parallelisms: List[str] = Field(default=[], description="Typological connections and parallelisms if explicitly present")
    summary: str = Field(..., description="Brief 2-3 sentence summary of the user's main thought")
    context_evaluation: ContextEvaluation = Field(..., description="Context evaluation result")


class TextItem(BaseTextItem):
    context_analysis: Optional[ContextAnalysisResult] = None


class BiblicalContextAnalyzer(TextProcessor):
    """Enhanced pipeline step: analyzes biblical context, extracts comprehensive structured information."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_api_model
        self.output_dir = settings.get_absolute_path(settings.output_dir)

    def run(self, item: TextItem) -> TextItem:
        # Detect user language from the input text
        user_language = self._detect_language(item.content)
        
        prompt = self._create_prompt(user_language)
        
        try:
            # Modern Responses API (2025 best practice)
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

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise

        # Create output folder
        now = datetime.now()
        today_time = now.strftime("%Y%m%d_%H%M")
        topic_folder = f"{today_time}_{result.topic.replace(' ', '')[:32]}"
        folder_path = self.output_dir / topic_folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # Save input and result
        input_path = folder_path / "input.txt"
        result_path = folder_path / "context_analysis.json"
        
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(item.content)
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        # Attach result to item for downstream pipeline
        item.context_analysis = result
        return item

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character patterns."""
        # Count Cyrillic characters
        cyrillic_count = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
        total_chars = len([char for char in text if char.isalpha()])
        
        if total_chars == 0:
            return "English"
        
        cyrillic_ratio = cyrillic_count / total_chars
        
        if cyrillic_ratio > 0.3:
            return "Russian"
        else:
            return "English"

    def _create_prompt(self, user_language: str) -> str:
        """Create detailed prompt for comprehensive biblical analysis."""
        return f"""
You are an expert biblical analyst. Extract comprehensive biblical context from the user's text and assess its sufficiency for podcast creation.

IMPORTANT REQUIREMENTS:
1. Extract ONLY what is explicitly present in the user's text - do not add external knowledge
2. For bible_references: provide biblical quotes in {user_language} (same language as user's text)
3. For topic: always use English (for folder naming)
4. For all other fields: use {user_language} (same language as user's text)

EXTRACTION GUIDELINES:
- topic: 2-5 words in English for folder naming
- bible_references: For each biblical mention or allusion:
  * reference: Standard biblical reference in {user_language} (e.g., "Genesis 1:1-31", "Бытие 1:1-31")
    ! for english language use King James Version (KJV), for russian language use Синодальный перевод (RST)
  * quotes: Biblical text in {user_language}, at least one sentence each, use ellipsis (...) for long passages
  * context: Brief explanation of what this verse/passage is about (not how it relates to user's text)
- keywords: Key terms and concepts from the user's text
- themes: Only theological, psychological, or historical themes explicitly present
- structure: Only if there's clear structure (repetition, climax, rhythm, logical progression)
- typologies_and_parallelisms: Only explicitly stated connections (like "six days of creation - six circuits of Jericho")
- summary: 2-3 sentence summary of user's main thought

CONTEXT SUFFICIENCY ASSESSMENT:
- is_context_sufficient: Set to true if the text contains enough material for a complete podcast (clear topic, biblical references, structured thought)
- completeness_score: Rate from 0.0 to 1.0 based on:
  * 0.8-1.0: Complete thought with clear structure, biblical references, and sufficient detail
  * 0.5-0.7: Partial thought with some missing elements but enough for basic podcast
  * 0.0-0.4: Incomplete thought requiring significant enrichment
- thought_completeness: 'complete' (0.8+), 'partial' (0.5-0.7), 'incomplete' (0.0-0.4)
- missing_elements: List what's missing (e.g., "biblical references", "clear structure", "key themes")
- enrichment_suggestions: Suggest what could be added (e.g., "add supporting Bible verses", "develop logical structure")

If any category has no clear examples in the text, leave it empty or null.
Focus on accuracy over completeness - better to extract less than to add what isn't there.
"""
