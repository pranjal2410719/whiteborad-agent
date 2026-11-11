"""Whiteboard tools and action handlers executable by AI agents and LLMs."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple

from .geometry import (
    calculate_sub_text_bounds,
    create_arrow_path,
    create_circle_path,
    create_underline_path,
)
from .mathcanvas import MathCanvasToolExtension
from .models import BoundingBox, WhiteboardElement
from .spatial_memory import SpatialMemory


class WhiteboardToolRegistry:
    """Registry of atomic operations on the whiteboard backed by SpatialMemory."""

    def __init__(self, spatial_memory: SpatialMemory):
        self.memory = spatial_memory
        self.mathcanvas = MathCanvasToolExtension(self.memory)

    # --- Tool 1: Write Text ---
    def write_text(
        self,
        text: str,
        title: Optional[str] = None,
        font_size: int = 16,
        color: str = "#1e293b",
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 240.0,
        height: float = 100.0,
    ) -> Dict[str, Any]:
        """Writes a block of text or markdown content on the canvas."""
        if x is None or y is None:
            # Deduplication check: return existing element if same text is already present
            for e in self.memory.elements.values():
                if e.type == "text" and e.content == text:
                    return {
                        "success": True,
                        "id": e.id,
                        "action": "write_text",
                        "bounds": e.bounds.to_dict(),
                        "message": f"Existing text block '{e.id}' reused",
                        "deduplicated": True,
                    }
            box = self.memory.find_empty_space(width, height, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=width, height=height)

        elem_id = f"txt-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=elem_id,
            type="text",
            bounds=box,
            title=title,
            content=text,
            style={"font_size": font_size, "color": color},
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": elem_id,
            "action": "write_text",
            "bounds": box.to_dict(),
            "message": f"Wrote text block '{elem_id}' at ({box.x}, {box.y})",
        }

    # --- Tool 2: Create Sticky Note ---
    def create_sticky_note(
        self,
        content: str,
        title: Optional[str] = "Note",
        color: Literal["yellow", "green", "pink", "blue", "orange"] = "yellow",
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 190.0,
        height: float = 140.0,
    ) -> Dict[str, Any]:
        """Creates a colored sticky note on the whiteboard."""
        color_map = {
            "yellow": "#fef08a",
            "green": "#bbf7d0",
            "pink": "#fbcfe8",
            "blue": "#bfdbfe",
            "orange": "#fed7aa",
        }
        bg = color_map.get(color, "#fef08a")

        if x is None or y is None:
            # Deduplication check: return existing element if same note is already present
            for e in self.memory.elements.values():
                if e.type == "sticky_note" and e.content == content:
                    return {
                        "success": True,
                        "id": e.id,
                        "action": "create_sticky_note",
                        "bounds": e.bounds.to_dict(),
                        "message": f"Existing sticky note '{e.id}' reused",
                        "deduplicated": True,
                    }
            box = self.memory.find_empty_space(width, height, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=width, height=height)

        elem_id = f"note-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=elem_id,
            type="sticky_note",
            bounds=box,
            title=title,
            content=content,
            style={"background": bg, "theme": color},
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": elem_id,
            "action": "create_sticky_note",
            "bounds": box.to_dict(),
            "message": f"Created sticky note '{elem_id}' with color {color}",
        }

    # --- Tool 3: Create Formula ---
    def create_formula(
        self,
        formula: str,
        title: Optional[str] = "Formula",
        steps: Optional[List[str]] = None,
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 260.0,
        height: float = 130.0,
    ) -> Dict[str, Any]:
        """Creates a mathematical formula or equation card with optional step-by-step resolution."""
        # Calculate spacious width so formula stays strictly on ONE line without congestion
        calc_width = width
        if calc_width == 260.0:
            calc_width = max(380.0, len(formula) * 22.0 + 90.0)

        calc_height = height
        if calc_height == 130.0:
            step_count = len(steps) if steps else 0
            calc_height = 85.0 + (step_count * 35.0) if step_count > 0 else 85.0

        if x is None or y is None:
            # Deduplication check: return existing element if same formula is already present
            for e in self.memory.elements.values():
                if e.type == "formula" and isinstance(e.content, dict) and e.content.get("formula") == formula:
                    return {
                        "success": True,
                        "id": e.id,
                        "action": "create_formula",
                        "bounds": e.bounds.to_dict(),
                        "message": f"Existing formula '{e.id}' reused: {formula}",
                        "deduplicated": True,
                    }
            box = self.memory.find_empty_space(calc_width, calc_height, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=calc_width, height=calc_height)

        elem_id = f"eq-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=elem_id,
            type="formula",
            bounds=box,
            title=title,
            content={"formula": formula, "steps": steps or []},
            style={"color": "#1e293b"},
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": elem_id,
            "action": "create_formula",
            "bounds": box.to_dict(),
            "message": f"Created formula '{elem_id}': {formula}",
        }

    # --- Tool 4: Create Diagram ---
    def create_diagram(
        self,
        nodes: Optional[List[Dict[str, str]]] = None,
        connections: Optional[List[Tuple[str, str]]] = None,
        title: Optional[str] = "Diagram",
        diagram_type: Literal["flowchart", "mindmap", "process"] = "flowchart",
        mermaid_code: Optional[str] = None,
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 300.0,
        height: float = 200.0,
    ) -> Dict[str, Any]:
        """Renders a flowchart or process diagram with connected steps, or from Mermaid syntax."""
        if mermaid_code:
            return self.create_mermaid(
                code=mermaid_code,
                title=title,
                anchor_id=anchor_id,
                direction=direction,
                x=x,
                y=y,
                width=width if width != 300.0 else None,
                height=height if height != 200.0 else None,
            )

        nodes = nodes or []
        if x is None or y is None:
            # Deduplication check: return existing element if same hint is already present
            for e in self.memory.elements.values():
                if e.type == "hint" and e.content == text:
                    return {
                        "success": True,
                        "id": e.id,
                        "action": "create_hint",
                        "bounds": e.bounds.to_dict(),
                        "message": f"Existing hint '{e.id}' reused",
                        "deduplicated": True,
                    }
            box = self.memory.find_empty_space(width, height, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=width, height=height)

        elem_id = f"diag-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=elem_id,
            type="diagram",
            bounds=box,
            title=title,
            content={
                "type": diagram_type,
                "nodes": nodes,
                "connections": connections or [],
            },
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": elem_id,
            "action": "create_diagram",
            "bounds": box.to_dict(),
            "message": f"Created diagram '{elem_id}' with {len(nodes)} nodes",
        }

    # --- Tool 4b: Create Mermaid Diagram ---
    def create_mermaid(
        self,
        code: str,
        title: Optional[str] = None,
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Renders any Mermaid flowchart, diagram, or graph (flowchart, sequence, state, class, ER, gitGraph, mindmap)."""
        clean_code = code.strip()
        lines = [l.strip() for l in clean_code.splitlines() if l.strip() and not l.strip().startswith("%%")]
        line_count = len(lines)
        first_line = lines[0].lower() if lines else ""

        is_horizontal = " lr" in first_line or "rl" in first_line
        is_sequence = "sequencediagram" in first_line

        calc_w = width
        calc_h = height
        if calc_w is None:
            if is_horizontal:
                calc_w = max(360.0, min(800.0, 200.0 + line_count * 55.0))
            elif is_sequence:
                calc_w = max(380.0, min(750.0, 220.0 + line_count * 40.0))
            else:
                max_line_len = max([len(l) for l in lines], default=20)
                calc_w = max(320.0, min(650.0, 180.0 + max_line_len * 7.0))

        if calc_h is None:
            if is_horizontal:
                calc_h = max(220.0, min(500.0, 140.0 + line_count * 30.0))
            elif is_sequence:
                calc_h = max(260.0, min(700.0, 120.0 + line_count * 45.0))
            else:
                calc_h = max(220.0, min(650.0, 100.0 + line_count * 45.0))

        if x is None or y is None:
            # Deduplication check: return existing element if same diagram code or title exists
            for e in self.memory.elements.values():
                if e.type == "mermaid" and isinstance(e.content, dict) and (e.content.get("code") == clean_code or (title and e.title == title)):
                    return {
                        "success": True,
                        "id": e.id,
                        "action": "create_mermaid",
                        "bounds": e.bounds.to_dict(),
                        "message": f"Existing Mermaid diagram '{e.id}' reused",
                        "deduplicated": True,
                    }
            box = self.memory.find_empty_space(calc_w, calc_h, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=calc_w, height=calc_h)

        elem_id = f"mrmd-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=elem_id,
            type="mermaid",
            bounds=box,
            title=title,
            content={
                "code": clean_code,
                "mermaid_code": clean_code,
            },
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": elem_id,
            "action": "create_mermaid",
            "bounds": box.to_dict(),
            "message": f"Created Mermaid diagram '{elem_id}' ({first_line[:20]})",
        }

    # --- Tool 5: Create Graph ---
    def create_graph(
        self,
        graph_type: Literal["function", "bar", "scatter", "coordinate_axes"] = "function",
        equation: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        title: Optional[str] = "Plot",
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 270.0,
        height: float = 170.0,
    ) -> Dict[str, Any]:
        """Plots a mathematical function curve or data chart with axes."""
        if x is None or y is None:
            # Deduplication check: return existing element if same hint is already present
            for e in self.memory.elements.values():
                if e.type == "hint" and e.content == text:
                    return {
                        "success": True,
                        "id": e.id,
                        "action": "create_hint",
                        "bounds": e.bounds.to_dict(),
                        "message": f"Existing hint '{e.id}' reused",
                        "deduplicated": True,
                    }
            box = self.memory.find_empty_space(width, height, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=width, height=height)

        elem_id = f"plot-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=elem_id,
            type="graph",
            bounds=box,
            title=title,
            content={
                "graph_type": graph_type,
                "equation": equation,
                "data": data or {},
            },
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": elem_id,
            "action": "create_graph",
            "bounds": box.to_dict(),
            "message": f"Created graph plot '{elem_id}' ({graph_type})",
        }

    # --- Tool 6: Create Hint ---
    def create_hint(
        self,
        text: str,
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 210.0,
        height: float = 90.0,
    ) -> Dict[str, Any]:
        """Creates a callout hint / tip card."""
        if x is None or y is None:
            # Deduplication check: return existing element if same hint is already present
            for e in self.memory.elements.values():
                if e.type == "hint" and e.content == text:
                    return {
                        "success": True,
                        "id": e.id,
                        "action": "create_hint",
                        "bounds": e.bounds.to_dict(),
                        "message": f"Existing hint '{e.id}' reused",
                        "deduplicated": True,
                    }
            box = self.memory.find_empty_space(width, height, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=width, height=height)

        elem_id = f"hint-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=elem_id,
            type="hint",
            bounds=box,
            title="Hint",
            content=text,
            style={"color": "#b45309"},
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": elem_id,
            "action": "create_hint",
            "bounds": box.to_dict(),
            "message": f"Created hint '{elem_id}'",
        }

    # --- Tool 7: Underline Element or Word/Term ---
    def underline_element(
        self,
        target_id: str,
        target_text: Optional[str] = None,
        color: str = "#dc2626",
        stroke_width: float = 3.0,
        style: Literal["straight", "wavy", "handdrawn"] = "handdrawn",
    ) -> Dict[str, Any]:
        """Draws an underline beneath a specific element, or beneath an exact word/formula term inside it."""
        # Deduplication: reuse existing underline on same target
        for e in self.memory.elements.values():
            if e.type == "stroke" and e.target_id == target_id and e.target_text == target_text and isinstance(e.content, dict) and e.content.get("stroke_type") == "underline":
                return {
                    "success": True,
                    "id": e.id,
                    "target_id": target_id,
                    "target_text": target_text,
                    "action": "underline_element",
                    "svg_path": e.content.get("svg_path"),
                    "bounds": e.bounds.to_dict(),
                    "message": f"Existing underline '{e.id}' reused",
                    "deduplicated": True,
                }

        target = self.memory.get_element(target_id)

        target_box = target.bounds
        if target_text:
            if isinstance(target.content, dict):
                full_text = target.content.get("code") or target.content.get("mermaid_code") or target.content.get("formula", "") or str(target.content)
            else:
                full_text = str(target.content or target.title or "")
            font_size = 36.0 if target.type == "formula" else 20.0 if target.type == "mermaid" else 24.0
            target_box = calculate_sub_text_bounds(target.bounds, full_text, target_text, font_size=font_size)

        path_data = create_underline_path(target_box, style=style)

        stroke_id = f"und-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=stroke_id,
            type="stroke",
            bounds=BoundingBox(**path_data["bounds"]),
            title=f"Underline on {target_id}" + (f" ('{target_text}')" if target_text else ""),
            content={
                "stroke_type": "underline",
                "svg_path": path_data["svg_path"],
                "points": path_data["points"],
                "target_text": target_text,
            },
            target_id=target_id,
            target_text=target_text,
            style={"color": color, "stroke_width": stroke_width},
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": stroke_id,
            "target_id": target_id,
            "target_text": target_text,
            "action": "underline_element",
            "svg_path": path_data["svg_path"],
            "bounds": elem.bounds.to_dict(),
            "message": f"Underlined {('term ' + repr(target_text) + ' inside ') if target_text else ''}'{target_id}' with {style} stroke",
        }

    # --- Tool 8: Circle Element or Word/Term ---
    def circle_element(
        self,
        target_id: str,
        target_text: Optional[str] = None,
        color: str = "#f59e0b",
        stroke_width: float = 3.0,
        padding: float = 8.0,
        style: Literal["smooth", "handdrawn"] = "handdrawn",
    ) -> Dict[str, Any]:
        """Draws an organic highlighter circle around an element, or around an exact word/formula term inside it."""
        # Deduplication: reuse existing circle on same target
        for e in self.memory.elements.values():
            if e.type == "stroke" and e.target_id == target_id and e.target_text == target_text and isinstance(e.content, dict) and e.content.get("stroke_type") == "circle":
                return {
                    "success": True,
                    "id": e.id,
                    "target_id": target_id,
                    "target_text": target_text,
                    "action": "circle_element",
                    "svg_path": e.content.get("svg_path"),
                    "bounds": e.bounds.to_dict(),
                    "message": f"Existing circle '{e.id}' reused",
                    "deduplicated": True,
                }

        target = self.memory.get_element(target_id)

        target_box = target.bounds
        if target_text:
            if isinstance(target.content, dict):
                full_text = target.content.get("code") or target.content.get("mermaid_code") or target.content.get("formula", "") or str(target.content)
            else:
                full_text = str(target.content or target.title or "")
            font_size = 36.0 if target.type == "formula" else 20.0 if target.type == "mermaid" else 24.0
            target_box = calculate_sub_text_bounds(target.bounds, full_text, target_text, font_size=font_size)

        circle_data = create_circle_path(target_box, padding=padding, style=style)

        stroke_id = f"circ-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=stroke_id,
            type="stroke",
            bounds=BoundingBox(**circle_data["bounds"]),
            title=f"Circle on {target_id}" + (f" ('{target_text}')" if target_text else ""),
            content={
                "stroke_type": "circle",
                "svg_path": circle_data["svg_path"],
                "center": circle_data["center"],
                "rx": circle_data["rx"],
                "ry": circle_data["ry"],
                "target_text": target_text,
            },
            target_id=target_id,
            target_text=target_text,
            style={"color": color, "stroke_width": stroke_width},
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": stroke_id,
            "target_id": target_id,
            "target_text": target_text,
            "action": "circle_element",
            "svg_path": circle_data["svg_path"],
            "bounds": elem.bounds.to_dict(),
            "message": f"Circled {('term ' + repr(target_text) + ' inside ') if target_text else ''}'{target_id}' with {style} stroke",
        }

    # --- Tool 9: Draw Arrow ---
    def draw_arrow(
        self,
        from_id: str,
        to_id: str,
        label: Optional[str] = None,
        color: str = "#6366f1",
        stroke_width: float = 2.5,
        style: Literal["straight", "curved"] = "curved",
    ) -> Dict[str, Any]:
        """Draws a directional arrow linking two elements on the whiteboard."""
        src = self.memory.get_element(from_id)
        dst = self.memory.get_element(to_id)
        arrow_data = create_arrow_path(src.bounds, dst.bounds, style=style)

        arrow_id = f"arr-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=arrow_id,
            type="stroke",
            bounds=BoundingBox(**arrow_data["bounds"]),
            title=label or f"Arrow {from_id} -> {to_id}",
            content={
                "stroke_type": "arrow",
                "from_id": from_id,
                "to_id": to_id,
                "label": label,
                "svg_path": arrow_data["svg_path"],
                "start": arrow_data["start"],
                "end": arrow_data["end"],
            },
            target_id=to_id,
            style={"color": color, "stroke_width": stroke_width},
        )
        self.memory.add_element(elem)
        return {
            "success": True,
            "id": arrow_id,
            "action": "draw_arrow",
            "from_id": from_id,
            "to_id": to_id,
            "svg_path": arrow_data["svg_path"],
            "message": f"Connected '{from_id}' to '{to_id}' with arrow",
        }

    # --- Tool 10: Annotate Element ---
    def annotate_element(
        self,
        target_id: str,
        text: str,
        position: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        color: str = "#8b5cf6",
    ) -> Dict[str, Any]:
        """Places an annotation callout beside target element with a connecting line."""
        target = self.memory.get_element(target_id)
        callout_w, callout_h = 160.0, 70.0
        box = self.memory.find_empty_space(callout_w, callout_h, anchor_id=target_id, direction=position)

        annot_id = f"ann-{uuid.uuid4().hex[:6]}"
        elem = WhiteboardElement(
            id=annot_id,
            type="annotation",
            bounds=box,
            title="Annotation",
            content=text,
            target_id=target_id,
            style={"color": color, "border": f"1.5px solid {color}", "background": "#faf5ff"},
        )
        self.memory.add_element(elem)

        # Also create connecting line stroke
        line_data = create_arrow_path(box, target.bounds, style="straight")
        stroke_id = f"annline-{uuid.uuid4().hex[:6]}"
        stroke = WhiteboardElement(
            id=stroke_id,
            type="stroke",
            bounds=BoundingBox(**line_data["bounds"]),
            content={"stroke_type": "leader_line", "svg_path": line_data["line_path"]},
            target_id=target_id,
            style={"color": color, "stroke_width": 1.5, "dash": [4, 4]},
        )
        self.memory.add_element(stroke)

        return {
            "success": True,
            "id": annot_id,
            "line_id": stroke_id,
            "target_id": target_id,
            "bounds": box.to_dict(),
            "message": f"Annotated element '{target_id}' with text: '{text}'",
        }

    # --- Tool 11: Pan / Drag Canvas Viewport ---
    def drag_canvas(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        zoom: Optional[float] = None,
        focus_element_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pans the whiteboard camera viewport to a coordinate or centers around a target element."""
        if focus_element_id:
            elem = self.memory.get_element(focus_element_id)
            target_x, target_y = elem.bounds.center
        else:
            target_x = x if x is not None else self.memory.viewport.x
            target_y = y if y is not None else self.memory.viewport.y

        self.memory.state.viewport.x = target_x
        self.memory.state.viewport.y = target_y
        if zoom is not None:
            self.memory.state.viewport.zoom = max(0.2, min(3.0, zoom))

        return {
            "success": True,
            "action": "drag_canvas",
            "viewport": {
                "x": self.memory.viewport.x,
                "y": self.memory.viewport.y,
                "zoom": self.memory.viewport.zoom,
            },
            "message": f"Panned canvas viewport to ({self.memory.viewport.x:.1f}, {self.memory.viewport.y:.1f}) @ {self.memory.viewport.zoom * 100:.0f}%",
        }

    # --- Tool 12: Move Element ---
    def move_element(
        self,
        element_id: str,
        x: float,
        y: float,
    ) -> Dict[str, Any]:
        """Moves an existing element to new coordinates after verifying collision status."""
        elem = self.memory.get_element(element_id)
        new_box = BoundingBox(x=x, y=y, width=elem.bounds.width, height=elem.bounds.height)
        colliders = self.memory.check_collision(new_box, exclude_id=element_id)
        if colliders:
            return {
                "success": False,
                "error": f"Collision detected at ({x}, {y}) with elements {colliders}",
                "colliders": colliders,
            }
        self.memory.update_element_bounds(element_id, x=x, y=y)
        return {
            "success": True,
            "id": element_id,
            "action": "move_element",
            "new_bounds": new_box.to_dict(),
            "message": f"Moved element '{element_id}' to ({x}, {y})",
        }

    # --- Tool 13: Delete Element ---
    def delete_element(self, element_id: str) -> Dict[str, Any]:
        """Deletes an element and any attached annotations/underlines/circles."""
        removed = self.memory.remove_element(element_id)
        if not removed:
            return {"success": False, "error": f"Element '{element_id}' does not exist"}

        # Cascade delete dependent strokes (like underline or arrows pointing to it)
        cascaded = []
        for sid, selem in list(self.memory.elements.items()):
            if selem.target_id == element_id:
                self.memory.remove_element(sid)
                cascaded.append(sid)

        return {
            "success": True,
            "id": element_id,
            "cascaded_removals": cascaded,
            "message": f"Deleted element '{element_id}' and {len(cascaded)} dependent strokes",
        }

    # --- Tool 14: Query Canvas State & Spatial Memory ---
    def get_canvas_state(self) -> Dict[str, Any]:
        """Returns the complete spatial summary of the canvas including all elements, coordinates, and bounds."""
        return self.memory.get_spatial_summary()

    # --- Tool 15: Find Empty Space ---
    def find_empty_space(
        self,
        width: float = 240.0,
        height: float = 140.0,
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
    ) -> Dict[str, Any]:
        """Calculates collision-free coordinates for content of given dimensions."""
        box = self.memory.find_empty_space(width, height, anchor_id=anchor_id, direction=direction)
        return {
            "success": True,
            "suggested_bounds": box.to_dict(),
            "message": f"Empty space found at ({box.x}, {box.y}) with size {width}x{height}",
        }

    # --- Tool 16: Clear Canvas ---
    def clear_canvas(self) -> Dict[str, Any]:
        """Clears all elements and resets viewport to origin."""
        count = len(self.memory.elements)
        self.memory.state.elements.clear()
        self.memory.state.viewport.x = 0.0
        self.memory.state.viewport.y = 0.0
        self.memory.state.viewport.zoom = 1.0
        self.memory.state.version += 1
        return {"success": True, "cleared_elements": count, "message": f"Cleared {count} elements from canvas"}

    # --- MathCanvas Tool 17: Construct Geometry (MathCanvas / AlphaGeometry) ---
    def construct_geometry(
        self,
        figure_type: Literal["triangle", "circle", "quadrilateral", "polygon", "coordinate_system"],
        points: Optional[Dict[str, Tuple[float, float]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        title: Optional[str] = "Geometric Construction",
        stroke_color: str = "#0f172a",
        anchor_id: Optional[str] = None,
        direction: Literal["auto", "right", "bottom", "left", "top"] = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 280.0,
        height: float = 220.0,
    ) -> Dict[str, Any]:
        """Constructs geometric figures with vertices, sides, and point labels directly in marker ink."""
        return self.mathcanvas.construct_geometry(
            figure_type=figure_type,
            points=points,
            parameters=parameters,
            title=title,
            stroke_color=stroke_color,
            anchor_id=anchor_id,
            direction=direction,
            x=x,
            y=y,
            width=width,
            height=height,
        )

    # --- MathCanvas Tool 18: Add Auxiliary Line (MathCanvas-Edit) ---
    def add_auxiliary_line(
        self,
        geometry_id: str,
        line_type: Literal["altitude", "median", "angle_bisector", "tangent", "segment", "perpendicular"],
        from_point: Optional[str] = None,
        to_point: Optional[str] = None,
        base_points: Optional[Tuple[str, str]] = None,
        label: str = "H",
        color: str = "#dc2626",
        style: Literal["dashed", "solid"] = "dashed",
    ) -> Dict[str, Any]:
        """Adds a strategic auxiliary construction line (altitude, median, tangent, angle bisector) to a geometry figure."""
        return self.mathcanvas.add_auxiliary_line(
            geometry_id=geometry_id,
            line_type=line_type,
            from_point=from_point,
            to_point=to_point,
            base_points=base_points,
            label=label,
            color=color,
            style=style,
        )

    # --- MathCanvas Tool 19: Mark Geometry (Right Angle / Congruence / Arc) ---
    def mark_geometry(
        self,
        geometry_id: str,
        mark_type: Literal["right_angle", "congruent_ticks", "angle_arc"],
        vertex: Optional[str] = None,
        arms: Optional[Tuple[str, str]] = None,
        segment: Optional[Tuple[str, str]] = None,
        ticks: int = 1,
        color: str = "#dc2626",
    ) -> Dict[str, Any]:
        """Marks right angles, congruence ticks, or angle arcs directly on a geometric drawing."""
        return self.mathcanvas.mark_geometry(
            geometry_id=geometry_id,
            mark_type=mark_type,
            vertex=vertex,
            arms=arms,
            segment=segment,
            ticks=ticks,
            color=color,
        )

    # --- MathCanvas Tool 20: Visual Chain-of-Thought (VCoT) Step ---
    def execute_vcot_step(
        self,
        thought: str,
        drawing_action: Optional[str] = None,
        drawing_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes an interleaved Visual Chain-of-Thought (VCoT) reasoning and drawing step."""
        return self.mathcanvas.execute_vcot_step(
            thought=thought,
            drawing_action=drawing_action,
            drawing_args=drawing_args,
        )
