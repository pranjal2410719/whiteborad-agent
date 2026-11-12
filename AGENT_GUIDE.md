# Whiteboard AI Agent · Complete Agent Guide & Integration Manual

> **Purpose**: This guide is written for AI agents, LLMs, and agent framework developers (LangChain, AutoGen, CrewAI, OpenAI Assistant, Anthropic Tool Use, Google GenAI, etc.) to efficiently, cleanly, and reliably interact with the Whiteboard AI Agent.

---

## 1. Agent Mental Model & Architecture

```
+-------------------------------------------------------------+
|                      Your Thinking LLM                      |
|       (OpenAI / Claude / Gemini / Ollama / DeepSeek / etc.) |
+------------------------------+------------------------------+
                               |
               1. Prompt + Spatial Digest Context
                               |
                               v
+-------------------------------------------------------------+
|                     WhiteboardAgent                         |
|                                                             |
|  +-----------------------+     +--------------------------+ |
|  |  SpatialMemory Engine |     |  WhiteboardToolRegistry  | |
|  |  - Bounding Box Math  |     |  - write_text            | |
|  |  - Collision Checks   |     |  - create_sticky_note    | |
|  |  - Empty Space Search |     |  - create_formula        | |
|  |  - Target Geometry    |     |  - create_diagram/graph  | |
|  |    (underline/circle) |     |  - underline/circle/arrow| |
|  +-----------------------+     +--------------------------+ |
|                                                             |
|  +-------------------------------------------------------+  |
|  |                   LLMToolAdapter                      |  |
|  |   Exports: OpenAI | Anthropic | Gemini | MCP Formats  |  |
|  +-------------------------------------------------------+  |
+------------------------------+------------------------------+
                               |
         2. Real-time Events (REST / WebSockets / DOM)
                               v
+-------------------------------------------------------------+
|               Interactive Whiteboard Canvas                 |
|            (web/index.html, tutor_work.html, SVG)           |
+-------------------------------------------------------------+
```

### The 5 Core Rules for the Agent

1. **Never Guess Coordinates Blindly**:
   - The whiteboard has an intelligent `SpatialMemory` engine.
   - To place an element relative to another, use `anchor_id` and `direction` (`"right"`, `"bottom"`, `"left"`, `"top"`).
   - If `x` and `y` are omitted, `SpatialMemory` automatically computes collision-free coordinates via Archimedean spiral raycasting.
2. **Always Reference Target IDs for Visual Accents**:
   - Do **not** calculate pixel coordinates to underline or circle an element.
   - Simply pass `target_id="el-123"` to `underline_element` or `circle_element`. The agent engine calculates exact SVG paths, bounding boxes, and offsets dynamically.
3. **Zero Overlaps & Dynamic Sizing**:
   - `SpatialMemory` enforces an 85px separation margin between all independent concepts.
   - Text, sticky notes, formulas, hints, and Mermaid diagrams automatically compute generous bounds matching real rendered DOM typography, guaranteeing that subsequent elements placed below or to the side never overlap.
   - Even if explicit `(x, y)` coordinates are supplied, the engine checks for collisions with 65px margin and shifts conflicting boxes to clear coordinates.
4. **Parameter Resiliency & Aliases**:
   - Tools accept `**kwargs` and handle parameter aliases seamlessly (`content` or `text`, `annotation_text` or `text`, `direction` or `position`, `formula` or `equation`), preventing runtime argument errors.
5. **Strict Zero-Emoji Policy**:
   - Maintain professional STEM pedagogical cleanliness: strictly avoid emojis across all whiteboard content, notes, titles, and agent responses. Use clean mathematical Unicode ($\Delta, \pi, \pm, \sqrt{}$) or LaTeX expressions.

---

## 2. Spatial Context Prompt Protocol

Before generating tool calls, the LLM should always receive the active **Spatial Memory Context** in its system or user prompt.

### Injecting Context in Python

```python
from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()

# Generate the prompt injection string
system_prompt = agent.get_system_prompt()
spatial_context = agent.get_spatial_context()

full_system_message = f"{system_prompt}\n\n{spatial_context}"
```

### What the Context Looks Like to the LLM:

```text
--- WHITEBOARD SPATIAL MEMORY ---
Active Elements (3):
  - [eq-d82a2c] FORMULA at (x:-120.0, y:74.0, w:260.0, h:130.0) | Content: "Quadratic Formula"
  - [und-cab2c3] STROKE at (x:-128.0, y:206.0, w:276.0, h:12.0) | Content: "Underline on eq-d82a2c" -> target: eq-d82a2c
  - [note-1f78f8] STICKY_NOTE at (x:164.0, y:74.0, w:190.0, h:140.0) | Content: "Check discriminant first..."
Viewport Camera: Center at (10.0, 139.0), Zoom: 110%
Tip: Use anchor_id and direction ('right'/'bottom') or call find_empty_space for collision-free placement.
---------------------------------
```

This context tells the LLM:
- Exactly which elements currently exist and what their IDs are.
- Their 2D bounds and content summaries.
- Where the camera is currently looking.

---

## 3. Complete Tool Catalog & Calling Reference

All tools return a consistent response object:
`{"success": bool, "id": str, "action": str, "bounds": {...}, "message": str}`

### 1. `write_text`
Writes a title, paragraph, or markdown text block on the board.
```json
{
  "text": "Introduction to Newton's Second Law",
  "title": "Topic 1",
  "font_size": 18,
  "color": "#0f172a",
  "anchor_id": null,
  "direction": "auto"
}
```

### 2. `create_sticky_note`
Creates a colored sticky note for tips, definitions, or reminders.
```json
{
  "content": "Remember: Force is a vector quantity with both magnitude and direction.",
  "title": "Key Concept",
  "color": "yellow",  // "yellow" | "green" | "pink" | "blue" | "orange"
  "anchor_id": "txt-01",
  "direction": "right"
}
```

### 3. `create_formula`
Renders a mathematical equation with step-by-step resolution lines.
```json
{
  "formula": "F = m * a",
  "title": "Newton's Second Law",
  "steps": [
    "F = Net force (Newtons, N)",
    "m = Mass (kg)",
    "a = Acceleration (m/s²)"
  ],
  "anchor_id": "txt-01",
  "direction": "bottom"
}
```

### 4. `create_diagram`
Generates a structured flowchart, process pipeline, or renders from Mermaid syntax directly.
```json
{
  "title": "Problem Solving Flow",
  "nodes": [
    {"label": "1. Identify known variables"},
    {"label": "2. Select governing formula"},
    {"label": "3. Solve for unknown"}
  ],
  "diagram_type": "flowchart",
  "direction": "bottom"
}
```
*Tip*: You can also pass `"mermaid_code"` directly to `create_diagram`!

### 4b. `create_mermaid` (Full Mermaid.js Ecosystem)
Renders any Mermaid flowchart, sequence diagram, state diagram, class diagram, ER diagram, gitGraph, or mindmap on the canvas with dry-erase whiteboard styling:
```json
{
  "title": "Quadratic Solver Decision Tree",
  "code": "graph TD\n  Start([Start: ax² + bx + c = 0]) --> Delta{Compute Δ = b² - 4ac}\n  Delta -->|Δ > 0| Real[Two Distinct Real Roots]\n  Delta -->|Δ = 0| Double[One Repeated Real Root]\n  Delta -->|Δ < 0| Complex[Two Complex Roots]\n  Real --> Finish([Factor Complete])\n  Double --> Finish\n  Complex --> Finish",
  "anchor_id": "eq-01",
  "direction": "bottom"
}
```
*Sub-element targeting*: You can call `underline_element` or `circle_element` targeting any node label or keyword inside the Mermaid diagram (e.g. `target_text="Two Distinct Real Roots"`).

### 5. `create_graph`
Draws mathematical function plots or bar charts with coordinate axes.
```json
{
  "graph_type": "function", // "function" | "bar" | "scatter" | "coordinate_axes"
  "equation": "y = x² - 4",
  "title": "Parabola with roots at ±2",
  "anchor_id": "eq-01",
  "direction": "right"
}
```

### 6. `create_hint`
Creates an attention-grabbing hint card.
```json
{
  "text": "Try factoring out (x - 2) first before expanding.",
  "anchor_id": "eq-01",
  "direction": "bottom"
}
```

### 7. `underline_element`
Draws an organic highlighter stroke directly below the target element.
```json
{
  "target_id": "eq-01",
  "color": "#e11d48",
  "style": "handdrawn" // "handdrawn" | "straight" | "wavy"
}
```

### 8. `circle_element`
Draws an organic highlighter loop surrounding the target element.
```json
{
  "target_id": "note-01",
  "color": "#f59e0b",
  "padding": 12.0,
  "style": "handdrawn" // "handdrawn" | "smooth"
}
```

### 9. `draw_arrow`
Connects two elements with a directional vector arrow.
```json
{
  "from_id": "eq-01",
  "to_id": "plot-01",
  "label": "Plots as",
  "color": "#6366f1",
  "style": "curved" // "curved" | "straight"
}
```

### 10. `annotate_element`
Places a callout note adjacent to an element with an attached dashed pointer line.
```json
{
  "target_id": "eq-01",
  "text": "This term represents the rate of change",
  "position": "auto" // "auto" | "right" | "top" | "bottom" | "left"
}
```

### 11. `drag_canvas`
Pans the camera viewport smoothly or focuses on a specific element.
```json
{
  "focus_element_id": "eq-01",
  "zoom": 1.2
}
```

### 12. `move_element`
Repositions an element to new coordinates with collision checking.
```json
{
  "element_id": "note-01",
  "x": 250.0,
  "y": 100.0
}
```

### 13. `delete_element`
Deletes an element and automatically cascade-deletes any attached underlines, circles, or pointing arrows.
```json
{
  "element_id": "note-01"
}
```

### 14. `find_empty_space`
Directly queries the spatial memory engine for free non-overlapping bounds.
```json
{
  "width": 240.0,
  "height": 140.0,
  "anchor_id": "eq-01",
  "direction": "right"
}
```

### 15. `get_canvas_state`
Returns the complete canvas JSON snapshot.
```json
{}
```

### 16. `clear_canvas`
Resets the whiteboard to a clean slate and centers the viewport.
```json
{}
```

### 17. `construct_geometry` (MathCanvas / AlphaGeometry)
Constructs geometric figures with vertices, sides, and point labels directly in marker ink.
```json
{
  "figure_type": "triangle", // "triangle" | "circle" | "quadrilateral" | "polygon" | "coordinate_system"
  "title": "Triangle ABC",
  "stroke_color": "#0f172a",
  "width": 300.0,
  "height": 220.0
}
```

### 18. `add_auxiliary_line` (MathCanvas-Edit)
Adds a strategic auxiliary construction line to an existing geometric figure with automatic markings (perpendicular right-angle square, midpoint ticks, angle arc).
```json
{
  "geometry_id": "geom-86ff93",
  "line_type": "altitude", // "altitude" | "median" | "angle_bisector" | "tangent" | "segment" | "perpendicular"
  "from_point": "A",
  "base_points": ["B", "C"],
  "label": "H",
  "color": "#dc2626",
  "style": "dashed"
}
```

### 19. `mark_geometry`
Draws right angles, congruence ticks, or angle arcs directly on a geometric drawing.
```json
{
  "geometry_id": "geom-86ff93",
  "mark_type": "right_angle", // "right_angle" | "congruent_ticks" | "angle_arc"
  "vertex": "A",
  "arms": ["B", "C"],
  "color": "#dc2626"
}
```

### 20. `execute_vcot_step`
Executes an interleaved Visual Chain-of-Thought (VCoT) reasoning and drawing step.
```json
{
  "thought": "Drop altitude AH perpendicular to BC to compute the triangle height.",
  "drawing_action": "add_auxiliary_line",
  "drawing_args": {
    "geometry_id": "geom-86ff93",
    "line_type": "altitude",
    "from_point": "A",
    "base_points": ["B", "C"],
    "label": "H"
  }
}
```

---

## 4. Standard Agent Layout Blueprints

For optimal visual presentation, follow these proven layout blueprints:

### Blueprint A: "The Concept Deep-Dive"
1. `write_text`: Lesson title and objective (top).
2. `create_formula`: Primary equation (`direction="bottom"`, anchored to title).
3. `underline_element`: Underline formula (`color="#e11d48"`).
4. `create_sticky_note`: Important rule or caveat (`direction="right"`, anchored to formula).
5. `circle_element`: Circle the sticky note (`color="#f59e0b"`).
6. `create_graph` or `create_diagram`: Visual demonstration (`direction="bottom"`).
7. `draw_arrow`: Link formula to graph (`label="Visualized"`).
8. `drag_canvas`: Focus camera on formula.

### Blueprint B: "Process / Algorithm Flow"
1. `write_text`: Algorithm or Workflow title.
2. `create_diagram`: Multi-step flow (`nodes=[...]`).
3. `annotate_element`: Highlight the tricky step with a callout.
4. `create_hint`: Add an exam tip or edge-case reminder below.

### Blueprint C: "MathCanvas Visual Chain-of-Thought (VCoT) Geometry"
1. `construct_geometry`: Construct base polygon / triangle (`figure_type="triangle"`, vertices $A, B, C$).
2. `add_auxiliary_line`: Drop altitude $AH \perp BC$ (automatically draws dashed line and $\llcorner$ right angle mark at $H$).
3. `add_auxiliary_line`: Add median $AM$ to $BC$ (automatically draws dashed line and $\parallel$ congruence ticks).
4. `mark_geometry`: Mark angle arc at $\angle BAC$.
5. `create_formula`: Derive analytical formula: $\text{Area}(\Delta ABC) = \frac{1}{2} \cdot BC \cdot AH$.
6. `underline_element`: Underline final theorem formula.
7. `drag_canvas`: Focus learner on construction.

---

## 5. End-to-End Agent Loop Implementations

### Python (OpenAI / OpenRouter / vLLM)

```python
import json
from openai import OpenAI
from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
client = OpenAI()

messages = [
    {
        "role": "system",
        "content": agent.get_system_prompt() + "\n\n" + agent.get_spatial_context(),
    },
    {"role": "user", "content": "Explain the quadratic formula on the whiteboard."},
]

while True:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=agent.get_tools_schema("openai"),
    )
    msg = response.choices[0].message
    messages.append(msg)

    if not msg.tool_calls:
        print("Final explanation:", msg.content)
        break

    for call in msg.tool_calls:
        tool_name = call.function.name
        tool_args = json.loads(call.function.arguments)
        print(f"Agent executing: {tool_name}")

        result = agent.execute_tool(tool_name, tool_args)

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "name": tool_name,
            "content": json.dumps(result),
        })

    # Update system message with updated spatial context
    messages[0]["content"] = agent.get_system_prompt() + "\n\n" + agent.get_spatial_context()
```

### Python (Anthropic Claude)

```python
import json
from anthropic import Anthropic
from whiteboard_agent import WhiteboardAgent

agent = WhiteboardAgent()
client = Anthropic()

messages = [{"role": "user", "content": "Draw the Pythagorean theorem and highlight it."}]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=agent.get_system_prompt() + "\n\n" + agent.get_spatial_context(),
    messages=messages,
    tools=agent.get_tools_schema("anthropic"),
)

for block in response.content:
    if block.type == "tool_use":
        result = agent.execute_tool(block.name, block.input)
        print("Executed:", block.name, "Result:", result)
```

### REST API Execution (Any Language: Node.js, Go, Python, cURL)

You can run the whiteboard server:
```bash
python3 -m whiteboard_agent --port 8000
```

Execute any operation via HTTP POST:
```bash
curl -X POST http://localhost:8000/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_sticky_note",
    "arguments": {
      "content": "Check your units (m/s) before solving!",
      "color": "pink"
    }
  }'
```

Query current spatial memory context:
```bash
curl http://localhost:8000/api/spatial
```

---

## 6. Error Handling & Edge Cases

| Scenario | Behavior | Recommended Agent Action |
|---|---|---|
| `Element 'xyz' not found` | Raised if `target_id` or `anchor_id` does not exist | Call `get_canvas_state()` or read the Spatial Context list to get valid element IDs. |
| Overcrowded canvas | `find_empty_space` automatically expands outward in larger spiral rings | Call `drag_canvas` to pan into the newly expanded territory or call `clear_canvas` if starting a new topic. |
| Collision on manual `move_element` | Returns `{"success": false, "error": "Collision detected..."}` | Omit explicit coordinates and let `find_empty_space` calculate the target bounds. |
| Cascading Deletes | Deleting an element automatically cleans up attached underlines, circles, and arrows | No need to delete strokes separately; deleting the parent card purges children safely. |
