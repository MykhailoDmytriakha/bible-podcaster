"""Base classes for pipeline stages and items."""
from __future__ import annotations

import abc
from typing import Any, Optional

from pydantic import BaseModel


class PipelineItem(BaseModel):
    """Base data model for items flowing through the pipeline."""

    id: Optional[str] = None


class PipelineStage(abc.ABC):
    """Abstract base class for a pipeline stage."""

    @abc.abstractmethod
    def run(self, item: PipelineItem) -> PipelineItem:
        """Process an item and return the result."""
        raise NotImplementedError


class Pipeline(abc.ABC):
    """Abstract base class for a pipeline."""

    def __init__(self) -> None:
        self.stages: list[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> None:
        self.stages.append(stage)

    def run(self, item: PipelineItem) -> PipelineItem:
        for stage in self.stages:
            item = stage.run(item)
        return item
