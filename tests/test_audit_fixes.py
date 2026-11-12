import pytest
from whiteboard_agent.agent import WhiteboardAgent
from whiteboard_agent.models import BoundingBox, WhiteboardElement


def test_diagram_and_graph_deduplication():
    agent = WhiteboardAgent()
    # 1. Test create_diagram deduplication (formerly crashed with NameError: name 'text' is not defined)
    res1 = agent.execute_tool(
        "create_diagram",
        {"title": "Test Diagram", "nodes": [{"id": "1", "label": "Start"}]}
    )
    assert res1["success"] is True
    diag_id = res1["id"]

    # Call again with identical nodes and title -> must deduplicate without crashing
    res2 = agent.execute_tool(
        "create_diagram",
        {"title": "Test Diagram", "nodes": [{"id": "1", "label": "Start"}]}
    )
    assert res2["success"] is True
    assert res2.get("deduplicated") is True
    assert res2["id"] == diag_id

    # Call with different connections/nodes -> must NOT deduplicate
    res2_diff = agent.execute_tool(
        "create_diagram",
        {"title": "Test Diagram", "nodes": [{"id": "1", "label": "Start"}], "connections": [("1", "2")]}
    )
    assert res2_diff["success"] is True
    assert res2_diff.get("deduplicated") is not True
    assert res2_diff["id"] != diag_id

    # 2. Test create_graph deduplication (formerly crashed with NameError)
    res3 = agent.execute_tool(
        "create_graph",
        {"title": "Sine Plot", "graph_type": "function", "equation": "sin(x)"}
    )
    assert res3["success"] is True
    plot_id = res3["id"]

    # Call again with identical equation and graph_type -> must deduplicate
    res4 = agent.execute_tool(
        "create_graph",
        {"title": "Sine Plot", "graph_type": "function", "equation": "sin(x)"}
    )
    assert res4["success"] is True
    assert res4.get("deduplicated") is True
    assert res4["id"] == plot_id

    # Two graphs with different data must NOT be falsely deduplicated
    res_bar1 = agent.execute_tool(
        "create_graph",
        {"graph_type": "bar", "data": {"apples": 10}}
    )
    res_bar2 = agent.execute_tool(
        "create_graph",
        {"graph_type": "bar", "data": {"bananas": 20}}
    )
    assert res_bar1["success"] is True
    assert res_bar2["success"] is True
    assert res_bar2.get("deduplicated") is not True
    assert res_bar2["id"] != res_bar1["id"]


def test_mathcanvas_kwargs_resilience():
    agent = WhiteboardAgent()
    # Test construct_geometry with vertices kwarg
    res1 = agent.execute_tool(
        "construct_geometry",
        {"figure_type": "triangle", "vertices": ["A", "B", "C"], "direction": "bottom"}
    )
    assert res1["success"] is True
    geom_id = res1["id"]
    pts = res1["points"]
    assert "A" in pts and "B" in pts and "C" in pts

    # Test mark_geometry with vertex and arms
    res2 = agent.execute_tool(
        "mark_geometry",
        {"geometry_id": geom_id, "mark_type": "right_angle", "vertex": "C", "arms": ["A", "B"]}
    )
    assert res2["success"] is True

    # Test add_auxiliary_line with from_vertex and to_segment
    res3 = agent.execute_tool(
        "add_auxiliary_line",
        {
            "geometry_id": geom_id,
            "line_type": "altitude",
            "from_vertex": "C",
            "to_segment": ["A", "B"]
        }
    )
    assert res3["success"] is True
    assert res3["label"] == "H"

    # Test right_triangle and rectangle constructions
    res_rt = agent.execute_tool(
        "construct_geometry",
        {"figure_type": "right_triangle", "vertices": ["A", "B", "C"]}
    )
    assert res_rt["success"] is True
    assert "A" in res_rt["points"] and "C" in res_rt["points"]

    res_rect = agent.execute_tool(
        "construct_geometry",
        {"figure_type": "rectangle", "vertices": ["A", "B", "C", "D"]}
    )
    assert res_rect["success"] is True
    assert len(res_rect["points"]) == 4

    # Test perpendicular with base_points
    res_perp = agent.execute_tool(
        "add_auxiliary_line",
        {
            "geometry_id": res_rt["id"],
            "line_type": "perpendicular",
            "from_point": "C",
            "base_points": ["A", "B"],
            "label": "P"
        }
    )
    assert res_perp["success"] is True
    assert res_perp["label"] == "P"


def test_spatial_memory_sync_no_displacement_no_inflation():
    agent = WhiteboardAgent()
    # Create formula element
    res_f = agent.execute_tool(
        "create_formula",
        {"title": "Pythagoras", "formula": "a^2 + b^2 = c^2", "x": 100.0, "y": 100.0, "width": 200.0, "height": 80.0}
    )
    formula_id = res_f["id"]

    # Underline formula
    res_u = agent.execute_tool(
        "underline_element",
        {"target_id": formula_id}
    )
    und_id = res_u["id"]
    und_elem = agent.memory.get_element(und_id)
    initial_und_y = und_elem.bounds.y

    # Circle formula
    res_c = agent.execute_tool(
        "circle_element",
        {"target_id": formula_id}
    )
    circ_id = res_c["id"]
    circ_elem = agent.memory.get_element(circ_id)
    initial_circ_w = circ_elem.bounds.width
    initial_circ_h = circ_elem.bounds.height

    # Move parent by dx=50, dy=0 five times
    for _ in range(5):
        agent.memory.update_element_bounds(formula_id, x=agent.memory.get_element(formula_id).bounds.x + 50.0, y=100.0)

    # Underline Y must NOT have drifted downwards
    final_und = agent.memory.get_element(und_id)
    assert final_und.bounds.y == pytest.approx(initial_und_y, abs=2.0)

    # Circle width and height must NOT have inflated
    final_circ = agent.memory.get_element(circ_id)
    assert final_circ.bounds.width == pytest.approx(initial_circ_w, abs=2.0)
    assert final_circ.bounds.height == pytest.approx(initial_circ_h, abs=2.0)
