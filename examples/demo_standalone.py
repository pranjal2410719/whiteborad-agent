"""Standalone demonstration of WhiteboardAgent with SpatialMemory and operations."""

from whiteboard_agent import WhiteboardAgent


def main():
    print("=== Initializing Whiteboard AI Agent ===")
    agent = WhiteboardAgent()

    # Step 1: Write introductory topic text
    res1 = agent.execute_tool("write_text", {
        "title": "Topic: Calculus - Power Rule",
        "text": "The power rule is the fundamental formula to find the derivative of monomials.",
        "font_size": 18,
    })
    print(f"1. {res1['message']}")

    # Step 2: Create mathematical formula (placed automatically next to or below previous element)
    res2 = agent.execute_tool("create_formula", {
        "title": "Power Rule Formula",
        "formula": "d/dx (x^n) = n * x^(n - 1)",
        "steps": [
            "1. Bring down the exponent n as a multiplier",
            "2. Subtract 1 from the power: n - 1",
            "Example: d/dx (x^3) = 3x^2",
        ],
        "anchor_id": res1["id"],
        "direction": "bottom",
    })
    eq_id = res2["id"]
    print(f"2. {res2['message']}")

    # Step 3: Draw an accurate underline stroke under the formula
    res3 = agent.execute_tool("underline_element", {
        "target_id": eq_id,
        "color": "#e11d48",
        "style": "handdrawn",
    })
    print(f"3. {res3['message']}")

    # Step 4: Create a sticky note with a tip (placed to the right of formula with zero collision)
    res4 = agent.execute_tool("create_sticky_note", {
        "title": "Crucial Shortcut",
        "content": "For constants c, d/dx (c) = 0 because it's equivalent to c * x^0.",
        "color": "yellow",
        "anchor_id": eq_id,
        "direction": "right",
    })
    note_id = res4["id"]
    print(f"4. {res4['message']}")

    # Step 5: Circle the sticky note with a yellow highlighter circle
    res5 = agent.execute_tool("circle_element", {
        "target_id": note_id,
        "color": "#f59e0b",
        "padding": 10.0,
    })
    print(f"5. {res5['message']}")

    # Step 6: Connect formula to sticky note with a directional arrow
    res6 = agent.execute_tool("draw_arrow", {
        "from_id": eq_id,
        "to_id": note_id,
        "label": "Applies to",
    })
    print(f"6. {res6['message']}")

    # Step 7: Create a flowchart diagram below the formula
    res7 = agent.execute_tool("create_diagram", {
        "title": "3-Step Differentiation Flow",
        "nodes": [
            {"label": "Identify power n"},
            {"label": "Multiply coefficient by n"},
            {"label": "Reduce exponent by 1"},
        ],
        "anchor_id": eq_id,
        "direction": "bottom",
    })
    print(f"7. {res7['message']}")

    # Step 8: Create a function plot graph to the right of diagram
    res8 = agent.execute_tool("create_graph", {
        "title": "Slope of Parabola y = x²",
        "equation": "y' = 2x",
        "graph_type": "function",
        "anchor_id": res7["id"],
        "direction": "right",
    })
    print(f"8. {res8['message']}")

    # Step 9: Pan canvas viewport to center on the new content
    res9 = agent.execute_tool("drag_canvas", {
        "focus_element_id": eq_id,
        "zoom": 1.1,
    })
    print(f"9. {res9['message']}")

    # Step 10: Inspect Spatial Memory digest
    print("\n=== Real-time Spatial Memory Digest (Provided to LLM) ===")
    print(agent.get_spatial_context())

    print("\n=== Total Canvas Elements Registered ===")
    print(f"Total elements: {len(agent.memory.elements)}")


if __name__ == "__main__":
    main()
