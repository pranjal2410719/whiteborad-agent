"""FastAPI + WebSocket server providing a real-time bridge for whiteboards and AI agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from .agent import WhiteboardAgent


class ToolExecutionRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


def create_whiteboard_app(agent: Optional[WhiteboardAgent] = None) -> FastAPI:
    """Creates a configured FastAPI application with WebSocket and REST APIs."""
    agent = agent or WhiteboardAgent()
    app = FastAPI(title="Whiteboard AI Agent API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Active websocket connections
    active_connections: List[WebSocket] = []

    # Wire agent listener to broadcast to connected clients
    def on_agent_event(event: Dict[str, Any]):
        msg = json.dumps(event)
        # Note: In async loop, send to active websockets
        import asyncio
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        if loop and loop.is_running():
            for ws in active_connections:
                loop.create_task(ws.send_text(msg))

    agent.add_listener(on_agent_event)

    @app.get("/api/state")
    def get_state():
        return {
            "version": agent.memory.state.version,
            "viewport": agent.memory.viewport.dict(),
            "elements": {k: v.dict() for k, v in agent.memory.elements.items()},
            "spatial_summary": agent.memory.get_spatial_summary(),
        }

    @app.get("/api/spatial")
    def get_spatial():
        return {
            "context_prompt": agent.get_spatial_context(),
            "summary": agent.memory.get_spatial_summary(),
        }

    @app.get("/api/tools")
    def get_tools(format: str = Query("openai", pattern="^(openai|anthropic|gemini|mcp)$")):
        return {
            "format": format,
            "tools": agent.get_tools_schema(format=format),
            "system_prompt": agent.get_system_prompt(),
        }

    @app.post("/api/tools/execute")
    def execute_tool(req: ToolExecutionRequest):
        res = agent.execute_tool(req.tool, req.arguments)
        return res

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        active_connections.append(websocket)
        try:
            # Send initial state snapshot
            await websocket.send_json({
                "event": "init_state",
                "version": agent.memory.state.version,
                "data": {
                    "elements": {k: v.dict() for k, v in agent.memory.elements.items()},
                    "viewport": agent.memory.viewport.dict(),
                },
            })

            while True:
                data = await websocket.receive_text()
                payload = json.loads(data)
                # Handle client-initiated action
                if payload.get("action") == "execute_tool":
                    tool = payload.get("tool")
                    args = payload.get("arguments", {})
                    result = agent.execute_tool(tool, args)
                    await websocket.send_json({
                        "event": "tool_result",
                        "tool": tool,
                        "result": result,
                    })
        except WebSocketDisconnect:
            if websocket in active_connections:
                active_connections.remove(websocket)
        except Exception:
            if websocket in active_connections:
                active_connections.remove(websocket)

    web_dir = Path(__file__).parent.parent / "web"
    index_file = web_dir / "index.html"
    bridge_file = web_dir / "bridge.js"
    mermaid_file = web_dir / "mermaid.min.js"

    @app.get("/mermaid.min.js")
    @app.get("/web/mermaid.min.js")
    def serve_mermaid():
        if mermaid_file.exists():
            return FileResponse(mermaid_file, media_type="application/javascript")
        return ""

    @app.get("/bridge.js")
    @app.get("/web/bridge.js")
    def serve_bridge():
        if bridge_file.exists():
            return FileResponse(bridge_file, media_type="application/javascript")
        return ""

    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        if index_file.exists():
            return FileResponse(index_file)
        return "<h1>Whiteboard AI Agent API Running</h1>"

    return app
