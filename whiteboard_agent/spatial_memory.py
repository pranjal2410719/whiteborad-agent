"""Spatial memory engine: tracks canvas geometry, collision avoidance, and empty space discovery."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple

from .models import BoundingBox, CanvasState, Viewport, WhiteboardElement


class SpatialMemory:
    """Manages spatial awareness, element occupancy, and free space discovery on the whiteboard."""

    def __init__(self, initial_state: Optional[CanvasState] = None):
        self.state = initial_state or CanvasState()
        self.default_margin: float = 85.0

    @property
    def elements(self) -> Dict[str, WhiteboardElement]:
        return self.state.elements

    @property
    def viewport(self) -> Viewport:
        return self.state.viewport

    def add_element(self, element: WhiteboardElement) -> WhiteboardElement:
        """Registers a new element in spatial memory."""
        self.state.elements[element.id] = element
        self.state.version += 1
        return element

    def update_element_bounds(self, element_id: str, x: float, y: float, width: Optional[float] = None, height: Optional[float] = None) -> WhiteboardElement:
        """Moves or resizes an element and automatically keeps all anchored strokes/arrows synchronized."""
        elem = self.get_element(element_id)
        dx = x - elem.bounds.x
        dy = y - elem.bounds.y

        new_w = width if width is not None else elem.bounds.width
        new_h = height if height is not None else elem.bounds.height
        elem.bounds = BoundingBox(x=x, y=y, width=new_w, height=new_h)

        # Synchronize all child strokes, underlines, circles, and arrows
        if dx != 0.0 or dy != 0.0:
            self._sync_dependents(element_id, dx, dy)

        self.state.version += 1
        return elem

    def _sync_dependents(self, parent_id: str, dx: float, dy: float) -> None:
        """Propagates movement to all dependent annotations, underlines, circles, and arrows."""
        from .geometry import (
            calculate_sub_text_bounds,
            create_arrow_path,
            create_circle_path,
            create_underline_path,
        )

        parent = self.state.elements.get(parent_id)

        for el in list(self.state.elements.values()):
            if el.target_id == parent_id or (isinstance(el.content, dict) and el.content.get("geometry_id") == parent_id):
                if isinstance(el.content, dict) and parent and el.target_id == parent_id:
                    st = el.content.get("stroke_type")
                    if st in ("underline", "circle"):
                        target_box = parent.bounds
                        if el.target_text:
                            if isinstance(parent.content, dict):
                                full_text = parent.content.get("code") or parent.content.get("mermaid_code") or parent.content.get("formula", "") or str(parent.content)
                            else:
                                full_text = str(parent.content or parent.title or "")
                            font_size = 36.0 if parent.type == "formula" else 20.0 if parent.type == "mermaid" else 24.0
                            target_box = calculate_sub_text_bounds(parent.bounds, full_text, el.target_text, font_size=font_size)

                        if st == "underline":
                            udata = create_underline_path(target_box, style=el.content.get("style", "handdrawn"))
                            el.content["svg_path"] = udata["svg_path"]
                            el.content["points"] = udata["points"]
                            el.bounds = BoundingBox(**udata["bounds"])
                        elif st == "circle":
                            cdata = create_circle_path(target_box, padding=el.content.get("padding", 8.0), style=el.content.get("style", "handdrawn"))
                            el.content["svg_path"] = cdata["svg_path"]
                            el.content["center"] = cdata["center"]
                            el.bounds = BoundingBox(**cdata["bounds"])
                    elif st == "arrow":
                        src_id = el.content.get("from_id")
                        dst_id = el.content.get("to_id")
                        if src_id in self.state.elements and dst_id in self.state.elements:
                            adata = create_arrow_path(self.state.elements[src_id].bounds, self.state.elements[dst_id].bounds)
                            el.content["svg_path"] = adata["svg_path"]
                            el.bounds = BoundingBox(**adata["bounds"])
                    else:
                        el.bounds = BoundingBox(
                            x=el.bounds.x + dx,
                            y=el.bounds.y + dy,
                            width=el.bounds.width,
                            height=el.bounds.height,
                        )
                else:
                    el.bounds = BoundingBox(
                        x=el.bounds.x + dx,
                        y=el.bounds.y + dy,
                        width=el.bounds.width,
                        height=el.bounds.height,
                    )

    def remove_element(self, element_id: str) -> Optional[WhiteboardElement]:
        """Removes an element from memory."""
        removed = self.state.elements.pop(element_id, None)
        if removed:
            self.state.version += 1
        return removed

    def get_element(self, element_id: str) -> WhiteboardElement:
        """Retrieves element by id or raises ValueError."""
        if element_id not in self.state.elements:
            available = list(self.state.elements.keys())
            raise ValueError(f"Element '{element_id}' not found. Available elements: {available}")
        return self.state.elements[element_id]

    def find_elements_by_text(self, query: str) -> List[WhiteboardElement]:
        """Searches for elements containing specific text, title, or tag."""
        q = query.lower()
        matches = []
        for el in self.state.elements.values():
            if el.title and q in el.title.lower() or isinstance(el.content, str) and q in el.content.lower() or any(q in tag.lower() for tag in el.tags):
                matches.append(el)
        return matches

    def check_collision(
        self,
        candidate_box: BoundingBox,
        margin: float = 65.0,
        exclude_id: Optional[str] = None,
        ignore_strokes: bool = True,
    ) -> List[str]:
        """Returns list of colliding element IDs if candidate_box intersects existing elements."""
        colliders = []
        for el_id, el in self.state.elements.items():
            if exclude_id and el_id == exclude_id:
                continue
            # Non-blocking strokes like underline or annotations can optionally be ignored for element placement
            if ignore_strokes and el.type in ("stroke",):
                continue
            if candidate_box.intersects(el.bounds, margin=margin):
                colliders.append(el_id)
        return colliders

    def get_canvas_bounds(self) -> Optional[BoundingBox]:
        """Calculates the bounding envelope containing all elements."""
        if not self.state.elements:
            return None
        min_x = min(el.bounds.left for el in self.state.elements.values())
        min_y = min(el.bounds.top for el in self.state.elements.values())
        max_x = max(el.bounds.right for el in self.state.elements.values())
        max_y = max(el.bounds.bottom for el in self.state.elements.values())
        return BoundingBox(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)

    def find_empty_space(
        self,
        width: float,
        height: float,
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        margin: Optional[float] = None,
    ) -> BoundingBox:
        """Finds guaranteed empty, non-overlapping coordinates for a new element of size (width, height).

        Uses directional placement if requested, and falls back to radial spiral search
        around the anchor or canvas center.
        """
        gap = margin if margin is not None else self.default_margin

        if not self.state.elements:
            # First element on empty canvas: center neatly
            return BoundingBox(x=-width / 2.0, y=-height / 2.0, width=width, height=height)

        anchor_box: Optional[BoundingBox] = None
        if anchor_id:
            try:
                anchor_box = self.get_element(anchor_id).bounds
            except ValueError:
                anchor_box = None

        if not anchor_box:
            # Default to the most recently added non-stroke element
            non_strokes = [e for e in self.state.elements.values() if e.type != "stroke"]
            if non_strokes:
                anchor_box = non_strokes[-1].bounds

        # If directional preference is set and anchor exists, test primary slot
        if anchor_box:
            candidate_positions: List[Tuple[float, float]] = []
            if direction == "right":
                candidate_positions.extend([
                    (anchor_box.right + gap, anchor_box.top),
                    (anchor_box.right + gap, anchor_box.center_y - height / 2.0),
                    (anchor_box.right + gap, anchor_box.bottom - height),
                ])
            elif direction == "bottom":
                candidate_positions.extend([
                    (anchor_box.left, anchor_box.bottom + gap),
                    (anchor_box.center_x - width / 2.0, anchor_box.bottom + gap),
                    (anchor_box.right - width, anchor_box.bottom + gap),
                ])
            elif direction == "left":
                candidate_positions.extend([
                    (anchor_box.left - width - gap, anchor_box.top),
                    (anchor_box.left - width - gap, anchor_box.center_y - height / 2.0),
                ])
            elif direction == "top":
                candidate_positions.extend([
                    (anchor_box.left, anchor_box.top - height - gap),
                    (anchor_box.center_x - width / 2.0, anchor_box.top - height - gap),
                ])
            elif direction == "auto":
                # Try right first (natural reading/board order), then bottom, then left, then top
                candidate_positions.extend([
                    (anchor_box.right + gap, anchor_box.top),
                    (anchor_box.left, anchor_box.bottom + gap),
                    (anchor_box.right + gap, anchor_box.center_y - height / 2.0),
                    (anchor_box.center_x - width / 2.0, anchor_box.bottom + gap),
                    (anchor_box.left - width - gap, anchor_box.top),
                    (anchor_box.left, anchor_box.top - height - gap),
                ])

            for cx, cy in candidate_positions:
                box = BoundingBox(x=round(cx, 1), y=round(cy, 1), width=width, height=height)
                if not self.check_collision(box, margin=gap):
                    return box

        # Spiral search around center of anchor (or canvas centroid)
        if anchor_box:
            origin_x, origin_y = anchor_box.center
        else:
            bounds = self.get_canvas_bounds()
            origin_x, origin_y = bounds.center if bounds else (0.0, 0.0)

        # Archimedean spiral search with step size adapted to element dimensions
        step_radius = max(35.0, min(width, height) * 0.35)
        for ring in range(1, 45):
            r = ring * step_radius
            steps = max(10, int(2 * math.pi * r / 50))
            for i in range(steps):
                angle = (2 * math.pi / steps) * i
                # Horizontal bias (1.35x) because whiteboards flow left-to-right
                cx = origin_x + math.cos(angle) * r * 1.35 - (width / 2.0)
                cy = origin_y + math.sin(angle) * r - (height / 2.0)
                box = BoundingBox(x=round(cx, 1), y=round(cy, 1), width=width, height=height)
                if not self.check_collision(box, margin=gap):
                    return box

        # Fallback: place cleanly far right of everything with generous margin
        bounds = self.get_canvas_bounds()
        assert bounds is not None
        return BoundingBox(x=bounds.right + gap, y=bounds.top, width=width, height=height)

    def get_spatial_summary(self) -> Dict[str, Any]:
        """Provides high-level spatial digest for LLMs to reason about whiteboard layout."""
        bounds = self.get_canvas_bounds()
        element_summaries = [el.to_summary() for el in self.state.elements.values()]

        return {
            "total_elements": len(self.state.elements),
            "canvas_extent": bounds.to_dict() if bounds else None,
            "viewport": {
                "center_x": self.state.viewport.x,
                "center_y": self.state.viewport.y,
                "zoom": self.state.viewport.zoom,
            },
            "elements": element_summaries,
            "element_ids": list(self.state.elements.keys()),
        }
