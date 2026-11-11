"""MathCanvas Visual Chain-of-Thought (VCoT) Demonstration.

Shows how an AI Agent interleaves step-by-step mathematical reasoning with
pure-pen geometric constructions and dynamic auxiliary line modifications.
"""

from whiteboard_agent import WhiteboardAgent


def main():
    print("=== MathCanvas: Intrinsic Visual Chain-of-Thought (VCoT) ===")
    agent = WhiteboardAgent()

    # Step 1: Text statement & Initial geometric figure construction
    print("\n[Step 1] Constructing primary geometric figure: Triangle ABC...")
    geom = agent.execute_tool("construct_geometry", {
        "figure_type": "triangle",
        "title": "Triangle ABC",
        "stroke_color": "#0f172a",
        "width": 300.0,
        "height": 220.0,
    })
    geom_id = geom["id"]
    print(f"✓ Created {geom['figure_type']} '{geom_id}' with vertices: {list(geom['points'].keys())}")

    # Step 2: VCoT deduction + Dropping an auxiliary altitude from A to base BC
    print("\n[Step 2] VCoT Reasoning: Drop altitude AH perpendicular to BC...")
    alt = agent.execute_tool("add_auxiliary_line", {
        "geometry_id": geom_id,
        "line_type": "altitude",
        "from_point": "A",
        "base_points": ("B", "C"),
        "label": "H",
        "color": "#dc2626",
        "style": "dashed",
    })
    print(f"✓ Added auxiliary altitude AH (id: {alt['id']}) with right-angle mark at H.")

    # Step 3: VCoT deduction + Adding auxiliary median AM from A to midpoint of BC
    print("\n[Step 3] VCoT Reasoning: Construct median AM bisecting segment BC at M...")
    med = agent.execute_tool("add_auxiliary_line", {
        "geometry_id": geom_id,
        "line_type": "median",
        "from_point": "A",
        "base_points": ("B", "C"),
        "label": "M",
        "color": "#2563eb",
        "style": "dashed",
    })
    print(f"✓ Added auxiliary median AM (id: {med['id']}) with congruence tick marks on BM and MC.")

    # Step 4: Angle marking at vertex A
    print("\n[Step 4] Marking angle BAC with angle arc...")
    arc = agent.execute_tool("mark_geometry", {
        "geometry_id": geom_id,
        "mark_type": "angle_arc",
        "vertex": "A",
        "arms": ("B", "C"),
        "color": "#7e22ce",
    })
    print(f"✓ Marked angle arc at vertex A (id: {arc['id']}).")

    # Step 5: Write mathematical deduction formula below
    print("\n[Step 5] Deriving Area Formula based on visual altitude AH...")
    f = agent.execute_tool("create_formula", {
        "title": "Area Derivation",
        "formula": "Area(ΔABC) = (1/2) * BC * AH",
        "steps": [
            "1. Base b = length(BC)",
            "2. Height h = length(AH)",
            "3. Split into two right triangles: ΔABH and ΔACH",
            "4. Sum of areas: (1/2)*BH*h + (1/2)*HC*h = (1/2)*(BH + HC)*h",
        ],
        "anchor_id": geom_id,
        "direction": "bottom",
    })
    print(f"✓ Wrote formula derivation (id: {f['id']}).")

    # Step 6: Underline final result
    agent.execute_tool("underline_element", {"target_id": f["id"], "color": "#dc2626"})
    print("✓ Underlined formula with pen stroke.")

    # Step 7: Camera focus
    agent.execute_tool("drag_canvas", {"focus_element_id": geom_id, "zoom": 1.1})
    print("✓ Panned viewport to center on the geometric construction.")

    print("\n=== Canvas Spatial Memory Digest ===")
    print(agent.get_spatial_context())


if __name__ == "__main__":
    main()
