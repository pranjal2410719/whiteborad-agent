"""Data models for whiteboard elements, spatial bounds, and canvas state."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """2D axis-aligned bounding box."""
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0

    @property
    def center(self) -> Tuple[float, float]:
        return (self.center_x, self.center_y)

    def intersects(self, other: BoundingBox, margin: float = 0.0) -> bool:
        """Returns True if this box overlaps with another box within the margin."""
        return not (
            self.right + margin <= other.left
            or self.left >= other.right + margin
            or self.bottom + margin <= other.top
            or self.top >= other.bottom + margin
        )

    def contains_point(self, px: float, py: float) -> bool:
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def expanded(self, margin: float) -> BoundingBox:
        return BoundingBox(
            x=self.x - margin,
            y=self.y - margin,
            width=self.width + 2 * margin,
            height=self.height + 2 * margin,
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
        }


ElementType = Literal[
    "text",
    "sticky_note",
    "formula",
    "diagram",
    "graph",
    "hint",
    "stroke",
    "annotation",
    "mermaid",
]


class WhiteboardElement(BaseModel):
    """A generic element on the canvas."""
    id: str = Field(default_factory=lambda: f"el-{uuid.uuid4().hex[:8]}")
    type: ElementType
    bounds: BoundingBox
    title: Optional[str] = None
    content: Any = ""
    z_index: int = 1
    style: Dict[str, Any] = Field(default_factory=dict)
    target_id: Optional[str] = None  # Reference to another element (for underline, circle, annotation)
    target_text: Optional[str] = None  # Exact sub-word, symbol, or term targeted inside the parent element
    anchor_offset: Optional[Tuple[float, float]] = None
    tags: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_summary(self) -> Dict[str, Any]:
        """Compact representation for LLM prompt context."""
        summary: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "bounds": self.bounds.to_dict(),
        }
        if self.title:
            summary["title"] = self.title
        if isinstance(self.content, str) and self.content:
            summary["preview"] = self.content[:60] + ("..." if len(self.content) > 60 else "")
        elif isinstance(self.content, dict):
            summary["keys"] = list(self.content.keys())
        if self.target_id:
            summary["target_id"] = self.target_id
        if self.target_text:
            summary["target_text"] = self.target_text
        return summary


class Viewport(BaseModel):
    """Camera position and zoom level of the canvas."""
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0


class CanvasState(BaseModel):
    """Full snapshot of the whiteboard state."""
    elements: Dict[str, WhiteboardElement] = Field(default_factory=dict)
    viewport: Viewport = Field(default_factory=Viewport)
    version: int = 0
