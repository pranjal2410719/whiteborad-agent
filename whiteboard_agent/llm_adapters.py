"""LLM adapters for OpenAI, Anthropic Claude, Google Gemini, Ollama, and MCP tool schemas."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List

from .tools import WhiteboardToolRegistry


def _python_type_to_json_schema(annotation: Any) -> Dict[str, Any]:
    """Maps Python type annotations to JSON Schema types."""
    import typing
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is typing.Union:
        # Check for Optional[T] (Union[T, NoneType])
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            schema = _python_type_to_json_schema(non_none[0])
            schema["nullable"] = True
            return schema
        return {"anyOf": [_python_type_to_json_schema(a) for a in non_none]}

    if origin is typing.Literal:
        return {"type": "string", "enum": list(args)}

    if origin is list or annotation is list:
        item_schema = _python_type_to_json_schema(args[0]) if args else {"type": "string"}
        return {"type": "array", "items": item_schema}

    if origin is dict or annotation is dict:
        return {"type": "object"}

    if annotation in (int,):
        return {"type": "integer"}
    if annotation in (float,):
        return {"type": "number"}
    if annotation in (bool,):
        return {"type": "boolean"}
    if annotation in (str,):
        return {"type": "string"}

    return {"type": "string"}


def tool_function_to_json_schema(fn: Callable) -> Dict[str, Any]:
    """Introspects a tool method to produce clean JSON Schema for tool calling."""
    sig = inspect.signature(fn)
    doc = inspect.getdoc(fn) or ""
    description = doc.split("\n\n")[0].strip() if doc else fn.__name__

    properties: Dict[str, Any] = {}
    required: List[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        prop_schema = _python_type_to_json_schema(param.annotation)
        # Extract default if present
        if param.default is inspect.Parameter.empty:
            required.append(name)
        properties[name] = prop_schema

    return {
        "name": fn.__name__,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


class LLMToolAdapter:
    """Exports Whiteboard tools into standard formats for all major AI models."""

    TOOL_NAMES = [
        "write_text",
        "create_sticky_note",
        "create_formula",
        "create_diagram",
        "create_mermaid",
        "create_graph",
        "create_hint",
        "underline_element",
        "circle_element",
        "draw_arrow",
        "annotate_element",
        "drag_canvas",
        "move_element",
        "delete_element",
        "get_canvas_state",
        "find_empty_space",
        "clear_canvas",
        "construct_geometry",
        "add_auxiliary_line",
        "mark_geometry",
        "execute_vcot_step",
    ]

    def __init__(self, registry: WhiteboardToolRegistry):
        self.registry = registry
        self._schemas = self._build_schemas()

    def _build_schemas(self) -> Dict[str, Dict[str, Any]]:
        schemas = {}
        for name in self.TOOL_NAMES:
            fn = getattr(self.registry, name, None)
            if fn and callable(fn):
                schemas[name] = tool_function_to_json_schema(fn)
        return schemas

    def to_openai(self) -> List[Dict[str, Any]]:
        """Returns tools in OpenAI function calling format."""
        tools = []
        for s in self._schemas.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": s["name"],
                    "description": s["description"],
                    "parameters": s["parameters"],
                },
            })
        return tools

    def to_anthropic(self) -> List[Dict[str, Any]]:
        """Returns tools in Anthropic Claude tool use format."""
        tools = []
        for s in self._schemas.values():
            tools.append({
                "name": s["name"],
                "description": s["description"],
                "input_schema": s["parameters"],
            })
        return tools

    def to_gemini(self) -> List[Dict[str, Any]]:
        """Returns tools in Google Gemini function declarations format."""
        tools = []
        for s in self._schemas.values():
            tools.append({
                "name": s["name"],
                "description": s["description"],
                "parameters": s["parameters"],
            })
        return tools

    def to_mcp(self) -> List[Dict[str, Any]]:
        """Returns tools in Model Context Protocol (MCP) format."""
        tools = []
        for s in self._schemas.values():
            tools.append({
                "name": s["name"],
                "description": s["description"],
                "inputSchema": s["parameters"],
            })
        return tools

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches and executes a tool call with error guarding."""
        if tool_name not in self._schemas:
            return {
                "success": False,
                "error": f"Unknown tool '{tool_name}'. Available: {list(self._schemas.keys())}",
            }
        handler = getattr(self.registry, tool_name)
        try:
            return handler(**arguments)
        except Exception as e:
            return {"success": False, "error": str(e), "tool": tool_name}
