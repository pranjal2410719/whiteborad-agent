"""Core Whiteboard AI Agent with spatial context injection and reactive event stream."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .llm_adapters import LLMToolAdapter
from .models import CanvasState
from .spatial_memory import SpatialMemory
from .tools import WhiteboardToolRegistry


class WhiteboardAgent:
    """The central Whiteboard AI Agent.

    Maintains spatial memory of the canvas, generates prompt context for any LLM,
    and provides function-calling execution with reactive event notifications.
    """

    def __init__(self, initial_state: Optional[CanvasState] = None):
        self.memory = SpatialMemory(initial_state)
        self.tools = WhiteboardToolRegistry(self.memory)
        self.adapter = LLMToolAdapter(self.tools)
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []

    def add_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribes a callback to receive real-time whiteboard events."""
        self._listeners.append(listener)

    def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        event = {
            "event": event_type,
            "version": self.memory.state.version,
            "data": data,
        }
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

    def get_system_prompt(self) -> str:
        """Returns instructions for any LLM describing how to act as a whiteboard agent."""
        return (
            "You are an expert Whiteboard AI Agent. Your role is to teach, explain, diagram, "
            "and visually organize concepts on a 2D canvas whiteboard.\n\n"
            "Key Principles:\n"
            "1. SPATIAL AWARENESS: You have complete spatial memory of every element on the board. "
            "Never place new content directly on top of existing elements. Use 'anchor_id' and 'direction' "
            "(e.g., 'right', 'bottom') or omit coordinates to let SpatialMemory automatically place items in clean empty spaces.\n"
            "2. TARGETED ANNOTATIONS: When highlighting, underlining, or drawing arrows, specify the 'target_id' "
            "of the element you are referencing. SpatialMemory will compute the exact mathematical paths.\n"
            "3. TEACHING FLOW: Mix formulas, diagrams, sticky notes, and graphs with visual cues (arrows, underlines, "
            "circles) to guide the learner's attention.\n"
            "4. CAMERA CONTROL: Use 'drag_canvas' or 'focus_element_id' to pan the learner's viewport to the current focus topic.\n"
        )

    def get_spatial_context(self) -> str:
        """Generates a real-time spatial memory report to append to the LLM's prompt."""
        summary = self.memory.get_spatial_summary()
        elements = summary["elements"]

        if not elements:
            return "--- WHITEBOARD STATE ---\nStatus: Clean empty canvas. Ready for initial content.\n-------------------------"

        lines = [
            "--- WHITEBOARD SPATIAL MEMORY ---",
            f"Active Elements ({len(elements)}):",
        ]
        for el in elements:
            b = el["bounds"]
            preview = el.get("preview", el.get("title", ""))
            target = f" -> target: {el['target_id']}" if "target_id" in el else ""
            lines.append(
                f"  - [{el['id']}] {el['type'].upper()} at (x:{b['x']}, y:{b['y']}, w:{b['width']}, h:{b['height']}) "
                f"| Content: \"{preview}\"{target}"
            )

        lines.append(
            f"Viewport Camera: Center at ({summary['viewport']['center_x']}, {summary['viewport']['center_y']}), "
            f"Zoom: {summary['viewport']['zoom'] * 100:.0f}%"
        )
        lines.append("Tip: Use anchor_id and direction ('right'/'bottom') or call find_empty_space for collision-free placement.")
        lines.append("---------------------------------")
        return "\n".join(lines)

    def get_tools_schema(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Returns tool declarations formatted for specified LLM provider."""
        fmt = format.lower()
        if fmt == "openai":
            return self.adapter.to_openai()
        elif fmt in ("anthropic", "claude"):
            return self.adapter.to_anthropic()
        elif fmt in ("gemini", "google"):
            return self.adapter.to_gemini()
        elif fmt == "mcp":
            return self.adapter.to_mcp()
        else:
            return self.adapter.to_openai()

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes tool, updates spatial memory, and emits event to listeners."""
        result = self.adapter.execute(tool_name, arguments)
        self._emit("tool_executed", {
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
        })
        return result

    def get_state(self) -> CanvasState:
        """Returns the full canvas state object."""
        return self.memory.state
