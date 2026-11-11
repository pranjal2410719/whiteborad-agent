"""Interactive Terminal CLI: Test Whiteboard AI Agent with live browser canvas sync."""

import json
import socket
import threading
import time
import urllib.request
import webbrowser
from typing import Any, Dict, Optional

import uvicorn

from whiteboard_agent import WhiteboardAgent, create_whiteboard_app


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def remote_call(port: int, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/tools/execute",
        data=json.dumps({"tool": tool, "arguments": arguments}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e), "message": f"Connection error: {e}"}


def remote_spatial_context(port: int) -> str:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/spatial", timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("context_prompt", "")
    except Exception as e:
        return f"Error retrieving spatial context: {e}"


def print_help():
    print("""
Available Commands:
  show / open                    - Open the live visual canvas in your browser
  formula <title> | <math>       - Create a math formula card
  underline [target_id]          - Underline last or specified element
  circle [target_id]             - Circle last or specified element
  note <title> | <content>       - Create a sticky note
  mermaid <title> | <code>       - Render any Mermaid diagram (flowchart, sequence, state, class)
  diagram <title> | <n1>,<n2>... - Create a multi-step flowchart
  graph <title> | <equation>     - Create a function plot (e.g. y = x²)
  hint <text>                    - Create a callout hint
  text <title> | <content>       - Write a text block
  arrow <from_id> <to_id>        - Draw arrow between two elements
  annotate <target_id> | <text>  - Attach annotation callout
  pan <element_id>               - Pan canvas camera to element
  list                           - List all elements and coordinates
  clear                          - Clear the whiteboard
  demo                           - Run automated teaching demo
  quit / exit                    - Exit CLI
""")


def main():
    port = 8000
    server_running = is_port_in_use(port)
    local_agent: Optional[WhiteboardAgent] = None

    if not server_running:
        local_agent = WhiteboardAgent()
        app = create_whiteboard_app(agent=local_agent)
        def run_srv():
            config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
            server = uvicorn.Server(config)
            server.run()

        srv_thread = threading.Thread(target=run_srv, daemon=True)
        srv_thread.start()
        time.sleep(0.4)
        print(f"📡 Live canvas server started at: http://localhost:{port}")
    else:
        print(f"📡 Connected to live running server at: http://localhost:{port}")

    def execute(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if server_running:
            return remote_call(port, tool_name, args)
        else:
            assert local_agent is not None
            return local_agent.execute_tool(tool_name, args)

    def get_spatial() -> str:
        if server_running:
            return remote_spatial_context(port)
        else:
            assert local_agent is not None
            return local_agent.get_spatial_context()

    last_id: Optional[str] = None

    print("=" * 64)
    print("🎨 Whiteboard AI Agent — Interactive Shell with Live Canvas Sync")
    print(f"👉 OPEN IN BROWSER TO SEE LIVE CANVAS: http://localhost:{port}")
    print("Type 'show' or 'open' to open the browser automatically.")
    print("Type 'help' for commands, 'demo' for auto-run, or 'quit' to exit.")
    print("=" * 64)

    while True:
        try:
            line = input("\n[Whiteboard] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not line:
            continue

        cmd = line.split()[0].lower()
        args = line[len(cmd):].strip()

        if cmd in ("quit", "exit"):
            print("Goodbye!")
            break
        elif cmd in ("show", "open", "browser"):
            url = f"http://localhost:{port}"
            print(f"Opening browser at {url} ...")
            webbrowser.open(url)
        elif cmd == "help":
            print_help()
        elif cmd == "list":
            print("\n" + get_spatial())
        elif cmd == "clear":
            res = execute("clear_canvas", {})
            last_id = None
            print(f"✓ {res.get('message', 'Cleared')}")
        elif cmd == "demo":
            print("\nRunning automated multi-element layout demo...")
            t = execute("write_text", {"title": "Calculus 101", "text": "Derivative of polynomials"})
            f = execute("create_formula", {"title": "Power Rule", "formula": "d/dx(x^n) = n*x^(n-1)", "anchor_id": t.get("id"), "direction": "bottom"})
            execute("underline_element", {"target_id": f.get("id")})
            n = execute("create_sticky_note", {"title": "Tip", "content": "Constant rule: d/dx(c) = 0", "anchor_id": f.get("id"), "direction": "right"})
            execute("circle_element", {"target_id": n.get("id")})
            execute("draw_arrow", {"from_id": f.get("id"), "to_id": n.get("id"), "label": "Key rule"})
            last_id = n.get("id")
            print(f"✓ Demo complete! Elements rendered live on canvas at http://localhost:{port}")
            print(get_spatial())
        elif cmd == "formula":
            parts = [p.strip() for p in args.split("|")]
            title = parts[0] if len(parts) > 1 else "Formula"
            f_str = parts[1] if len(parts) > 1 else parts[0]
            res = execute("create_formula", {"title": title, "formula": f_str})
            last_id = res.get("id")
            print(f"✓ Created formula '{last_id}': {f_str}")
            print(f"  👉 View live on canvas at: http://localhost:{port}")
        elif cmd == "underline":
            target = last_id
            word = None
            if args:
                tokens = args.split(maxsplit=1)
                if any(tokens[0].startswith(prefix) for prefix in ("eq-", "txt-", "note-", "geom-", "diag-", "plot-", "hint-")):
                    target = tokens[0]
                    word = tokens[1] if len(tokens) > 1 else None
                else:
                    word = args
            if not target:
                print("Error: No element to underline. Create a formula/note first.")
                continue
            res = execute("underline_element", {"target_id": target, "target_text": word})
            print(f"✓ {res.get('message', 'Underlined')}")
        elif cmd == "circle":
            target = last_id
            word = None
            if args:
                tokens = args.split(maxsplit=1)
                if any(tokens[0].startswith(prefix) for prefix in ("eq-", "txt-", "note-", "geom-", "diag-", "plot-", "hint-")):
                    target = tokens[0]
                    word = tokens[1] if len(tokens) > 1 else None
                else:
                    word = args
            if not target:
                print("Error: No element to circle. Create a formula/note first.")
                continue
            res = execute("circle_element", {"target_id": target, "target_text": word})
            print(f"✓ {res.get('message', 'Circled')}")
        elif cmd == "move":
            tokens = args.split()
            if len(tokens) < 3:
                print("Usage: move <element_id> <x> <y>")
                continue
            res = execute("move_element", {"element_id": tokens[0], "x": float(tokens[1]), "y": float(tokens[2])})
            print(f"✓ {res.get('message', 'Moved element')}")
        elif cmd == "note":
            parts = [p.strip() for p in args.split("|")]
            title = parts[0] if len(parts) > 1 else "Sticky Note"
            content = parts[1] if len(parts) > 1 else parts[0]
            res = execute("create_sticky_note", {"title": title, "content": content})
            last_id = res.get("id")
            print(f"✓ {res.get('message', 'Created note')} (id: {last_id})")
        elif cmd == "mermaid":
            parts = [p.strip() for p in args.split("|")]
            title = parts[0] if len(parts) > 1 else "Flowchart"
            code = parts[1] if len(parts) > 1 else parts[0]
            if "\n" not in code and ";" in code:
                code = "\n".join([s.strip() for s in code.split(";") if s.strip()])
            res = execute("create_mermaid", {"title": title, "code": code})
            last_id = res.get("id")
            print(f"✓ {res.get('message', 'Created Mermaid diagram')} (id: {last_id})")
            print(f"  👉 View live on canvas at: http://localhost:{port}")
        elif cmd == "diagram":
            parts = [p.strip() for p in args.split("|")]
            title = parts[0] if len(parts) > 1 else "Flowchart"
            nodes_str = parts[1] if len(parts) > 1 else "Step 1,Step 2,Step 3"
            nodes = [{"label": s.strip()} for s in nodes_str.split(",")]
            res = execute("create_diagram", {"title": title, "nodes": nodes})
            last_id = res.get("id")
            print(f"✓ {res.get('message', 'Created diagram')} (id: {last_id})")
        elif cmd == "graph":
            parts = [p.strip() for p in args.split("|")]
            title = parts[0] if len(parts) > 1 else "Plot"
            eq = parts[1] if len(parts) > 1 else "y = x^2"
            res = execute("create_graph", {"title": title, "equation": eq})
            last_id = res.get("id")
            print(f"✓ {res.get('message', 'Created graph')} (id: {last_id})")
        elif cmd == "hint":
            res = execute("create_hint", {"text": args or "Check your signs!"})
            last_id = res.get("id")
            print(f"✓ {res.get('message', 'Created hint')} (id: {last_id})")
        elif cmd == "text":
            parts = [p.strip() for p in args.split("|")]
            title = parts[0] if len(parts) > 1 else "Text"
            content = parts[1] if len(parts) > 1 else parts[0]
            res = execute("write_text", {"title": title, "text": content})
            last_id = res.get("id")
            print(f"✓ {res.get('message', 'Created text')} (id: {last_id})")
        elif cmd == "arrow":
            tokens = args.split()
            if len(tokens) < 2:
                print("Usage: arrow <from_id> <to_id>")
                continue
            res = execute("draw_arrow", {"from_id": tokens[0], "to_id": tokens[1]})
            print(f"✓ {res.get('message', 'Connected arrow')}")
        elif cmd == "annotate":
            parts = [p.strip() for p in args.split("|")]
            target = parts[0] if len(parts) > 1 else last_id
            text = parts[1] if len(parts) > 1 else parts[0]
            if not target:
                print("Usage: annotate <target_id> | <text>")
                continue
            res = execute("annotate_element", {"target_id": target, "text": text})
            print(f"✓ {res.get('message', 'Annotated')}")
        elif cmd == "pan":
            target = args if args else last_id
            res = execute("drag_canvas", {"focus_element_id": target})
            print(f"✓ {res.get('message', 'Panned')}")
        else:
            print(f"Unknown command '{cmd}'. Type 'help' for command list.")


if __name__ == "__main__":
    main()
