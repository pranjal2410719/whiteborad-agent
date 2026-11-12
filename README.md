# Whiteboard AI Agent

A dedicated AI Agent and Spatial Memory Engine designed to autonomously operate on digital whiteboards and infinite canvases. Compatible with **any LLM** (OpenAI, Anthropic Claude, Google Gemini, Ollama / local models, LangChain, or MCP).

> **Looking for the Agent Integration Manual?**
> See [**`AGENT_GUIDE.md`**](file:///home/dev/Desktop/projects/Qrie-Org/tutor/whiteboard_agent/AGENT_GUIDE.md) for complete agent protocols, spatial memory rules, layout blueprints, and multi-turn execution loops.

---

## Core Highlights

1. **Spatial Memory & Zero-Overlap Guarantee Engine**:
   - Tracks 2D bounding boxes `(x, y, width, height)` of every element on the canvas.
   - Dynamic size calculation: character-aware multi-line width and height calculation for text, sticky notes, formulas, hints, and Mermaid diagrams prevents undersized bounding boxes.
   - Guaranteed collision-free empty space finder using directional placement (`right`, `bottom`, `left`, `top`) with generous 85px separation margin, multi-tier slot alignment, and Archimedean spiral raycasting.
   - Collision checks run even when explicit `(x, y)` coordinates are supplied, automatically relocating colliding inputs to nearby clear space.
   - Generates compact spatial context digests injected directly into LLM prompts so thinking models have spatial awareness.

2. **Accurate Target Geometry Operations**:
   - `underline_element(target_id)`: Generates precise SVG paths positioned right beneath the target text/card with organic hand-drawn styling and clean vertical offset.
   - `circle_element(target_id)`: Calculates bounding oval coordinates with padding to highlight elements or specific sub-terms without clipping adjacent characters.
   - `draw_arrow(from_id, to_id)`: Dynamically computes closest exit and entry edge anchors with arrowhead geometry.
   - `annotate_element(target_id, text)`: Finds free space next to the target and attaches an annotation badge with a leader line.

3. **MathCanvas Powered Visual Chain-of-Thought (VCoT)**:
   - Implements the intrinsic multimodal mathematical reasoning paradigm from **MathCanvas (ACL 2026, CUHK MMLab & Huawei Research)**.
   - `construct_geometry`: Foundational geometric structures based on AlphaGeometry (triangles, right triangles, rectangles, circles, coordinate axes).
   - `add_auxiliary_line`: Dynamic visual editing (altitudes with right-angle squares, medians with congruence ticks, angle bisectors, perpendiculars, tangents).
   - `mark_geometry`: Right-angle squares ($\llcorner$), congruent segment ticks ($\parallel$), and angle arcs.
   - `execute_vcot_step`: Interleaves textual deductive reasoning with real-time visual diagram modifications.

4. **First-Class Mermaid.js Diagrams & Flowcharts**:
   - `create_mermaid(code, title)`: Full support for the complete [Mermaid.js](https://github.com/mermaid-js/mermaid) grammar directly on the whiteboard.
   - Flowcharts (`flowchart TD` / `graph LR`), Sequence Diagrams, State Diagrams, Class Diagrams, ER Diagrams, Timelines, Git Graphs, and Mindmaps.
   - Rendered with authentic dry-erase whiteboard typography and hand-drawn marker aesthetics.
   - Sub-element targeting: Call `circle_element` or `underline_element` on individual node labels or words inside Mermaid diagrams.

5. **Complete Whiteboard Tool Suite**:
   - `write_text`: Text blocks and titles with dynamic word-wrap bounds.
   - `create_sticky_note`: Sticky notes with themes and generous multi-line heights.
   - `create_formula`: Single-line formulas and equations with sub-word/term targeting.
   - `create_mermaid` & `create_diagram`: Mermaid charts and process trees.
   - `create_graph`: Function curves ($y = ax^2 + bx + c$), axes, plots.
   - `create_hint`: Callout hint cards.
   - `underline_element` & `circle_element`: Targeting elements or specific words/terms.
   - `drag_canvas`: Camera viewport pan, zoom, and auto-fit.
   - `move_element`, `delete_element`, `clear_canvas`.
   - `find_empty_space`, `get_canvas_state`.

6. **Robust Parameter Tolerance & Universal LLM Interoperability**:
   - Resilient parameter adaptation: all tools accept `**kwargs` and seamlessly map LLM aliases (`text` <-> `content`, `annotation_text` <-> `text`, `direction` <-> `position`, `equation` <-> `formula`, etc.), eliminating tool execution runtime exceptions.
   - Strict zero-emoji policy: clean, distraction-free pedagogical presentation.
   - Compatible with **Pipecat AI** voice pipelines (TTS/STT) for synchronized audio micro-lectures.
   - Exports standard tool schemas:
     - **OpenAI Function Calling** (`tools: [{type: "function", ...}]`)
     - **Anthropic Claude Tool Use** (`tools: [{name: ..., input_schema: ...}]`)
     - **Google Gemini Function Declarations** (`function_declarations: [...]`)
     - **MCP (Model Context Protocol)** (`inputSchema: {...}`)
   - Built-in FastAPI + WebSocket server + `bridge.js` for real-time web canvas synchronization.

---

## Repository Structure

```
whiteboard_agent/
├── pyproject.toml              # Package configuration
├── whiteboard_agent/
│   ├── models.py               # BoundingBox, WhiteboardElement, CanvasState, Viewport
│   ├── spatial_memory.py       # SpatialMemory: collision detection & empty space search
│   ├── geometry.py             # Precise underline, circle, arrow, and SVG paths
│   ├── mathcanvas.py           # MathCanvas VCoT: foundational geometry & auxiliary lines
│   ├── tools.py                # 20 whiteboard operations & tool execution handlers
│   ├── llm_adapters.py         # OpenAI, Claude, Gemini, MCP tool format adapters
│   ├── agent.py                # Central WhiteboardAgent class & prompt context builder
│   ├── server.py               # FastAPI + WebSocket server for live canvases
│   └── __main__.py             # CLI runner (python -m whiteboard_agent)
├── web/
│   ├── index.html              # Interactive canvas viewer with live agent test bench
│   └── bridge.js               # Universal JavaScript bridge for any web canvas
├── examples/
│   ├── demo_standalone.py      # Standalone spatial layout demonstration
│   ├── demo_openai.py          # OpenAI function calling example
│   ├── demo_anthropic.py       # Anthropic Claude tool use example
│   ├── demo_gemini.py          # Google Gemini function declarations example
│   └── demo_local_ollama.py    # Local LLMs via Ollama example
└── tests/                      # Pytest suite (23 passing tests)
```

---

## Quickstart

### 1. Installation

```bash
cd whiteboard_agent
pip install -e .
```

### 2. Standalone Python Usage

```python
from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()

# 1. Place a formula (automatically placed at empty space)
eq = agent.execute_tool("create_formula", {
    "title": "Quadratic Formula",
    "formula": "x = (-b ± √(b² - 4ac)) / 2a",
    "steps": ["Compute discriminant Δ", "Find roots x1, x2"]
})

# 2. Underline the formula accurately using target_id
agent.execute_tool("underline_element", {
    "target_id": eq["id"],
    "color": "#e11d48",
    "style": "handdrawn"
})

# 3. Place a sticky note to the right of the formula (no collision)
note = agent.execute_tool("create_sticky_note", {
    "title": "Key Rule",
    "content": "If Δ < 0, there are no real roots!",
    "anchor_id": eq["id"],
    "direction": "right"
})

# 4. Highlight the sticky note with a circle
agent.execute_tool("circle_element", {
    "target_id": note["id"],
    "color": "#f59e0b"
})

# 5. Pan the canvas camera to focus on the formula
agent.execute_tool("drag_canvas", {
    "focus_element_id": eq["id"],
    "zoom": 1.2
})
```

---

## Providing to Any LLM

### OpenAI Function Calling

```python
from openai import OpenAI
from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
client = OpenAI()

messages = [
    {"role": "system", "content": agent.get_system_prompt() + "\n" + agent.get_spatial_context()},
    {"role": "user", "content": "Explain Pythagorean theorem on the whiteboard with a diagram and highlight the formula."}
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=agent.get_tools_schema("openai"),
)

for call in response.choices[0].message.tool_calls or []:
    result = agent.execute_tool(call.function.name, json.loads(call.function.arguments))
```

### Anthropic Claude Tool Use

```python
from anthropic import Anthropic
from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
client = Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=agent.get_system_prompt() + "\n" + agent.get_spatial_context(),
    messages=[{"role": "user", "content": "Draw the power rule with a plot and highlight it."}],
    tools=agent.get_tools_schema("anthropic"),
)
```

### Google Gemini Function Declarations

```python
from google import genai
from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Draw a 3-step differentiation flowchart on the canvas",
    config={
        "system_instruction": agent.get_system_prompt() + "\n" + agent.get_spatial_context(),
        "tools": [{"function_declarations": agent.get_tools_schema("gemini")}],
    }
)
```

---

## Running the Interactive Web Whiteboard Server

Start the local server:

```bash
python3 -m whiteboard_agent --port 8000
```

Open `http://localhost:8000` in your browser. You can:
- See the infinite canvas with panning and zooming.
- Click operations in the sidebar to simulate tools.
- Watch strokes, sticky notes, formulas, graphs, and annotations render in real time.
- Connect your own LLM backend to `POST /api/tools/execute` or stream via `ws://localhost:8000/ws`.

---

## Testing

Run the test suite:

```bash
pytest
```
All 23 test suites verify spatial memory bounds, collision avoidance, geometry path generation, tool registry execution, MathCanvas VCoT, and schema formats.
