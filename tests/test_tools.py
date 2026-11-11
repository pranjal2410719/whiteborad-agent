"""Tests for all Whiteboard operations and tool registry."""

from whiteboard_agent.spatial_memory import SpatialMemory
from whiteboard_agent.tools import WhiteboardToolRegistry


def test_tool_write_text_and_formula():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    t_res = reg.write_text("Hello whiteboard", title="Intro")
    assert t_res["success"] is True
    assert "txt-" in t_res["id"]

    f_res = reg.create_formula("E = mc²", title="Mass Energy")
    assert f_res["success"] is True
    assert "eq-" in f_res["id"]


def test_targeting_strokes_underline_and_circle():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    note = reg.create_sticky_note("Critical rule", title="Exam Tip")
    nid = note["id"]

    # Underline
    u_res = reg.underline_element(target_id=nid)
    assert u_res["success"] is True
    assert u_res["target_id"] == nid
    assert "svg_path" in u_res

    # Circle
    c_res = reg.circle_element(target_id=nid)
    assert c_res["success"] is True
    assert c_res["target_id"] == nid

    # Cascading delete
    del_res = reg.delete_element(nid)
    assert del_res["success"] is True
    # The strokes targeting nid should be cascade deleted
    assert u_res["id"] not in mem.elements
    assert c_res["id"] not in mem.elements


def test_diagram_graph_and_pan():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    d_res = reg.create_diagram([{"label": "Step 1"}, {"label": "Step 2"}], title="Algorithm")
    assert d_res["success"] is True

    g_res = reg.create_graph(equation="y = 2x + 1", graph_type="function")
    assert g_res["success"] is True

    pan_res = reg.drag_canvas(focus_element_id=g_res["id"], zoom=1.5)
    assert pan_res["success"] is True
    assert mem.viewport.zoom == 1.5


def test_word_targeting_and_motion_synchronization():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    # 1. Create formula ax² + bx + c = 0
    f_res = reg.create_formula("ax² + bx + c = 0", title="Quadratic Formula")
    fid = f_res["id"]

    # 2. Underline ONLY 'bx'
    u_res = reg.underline_element(target_id=fid, target_text="bx")
    assert u_res["success"] is True
    assert u_res["target_text"] == "bx"
    orig_u_x = u_res["bounds"]["x"]

    # 3. Circle ONLY 'c'
    c_res = reg.circle_element(target_id=fid, target_text="c")
    assert c_res["success"] is True
    assert c_res["target_text"] == "c"
    orig_c_x = c_res["bounds"]["x"]

    # 4. Move formula by (+50, +30)
    move_res = reg.move_element(fid, x=f_res["bounds"]["x"] + 50.0, y=f_res["bounds"]["y"] + 30.0)
    assert move_res["success"] is True

    # 5. Check that underline and circle moved along in perfect synchronization
    u_elem = mem.get_element(u_res["id"])
    c_elem = mem.get_element(c_res["id"])
    assert round(u_elem.bounds.x - orig_u_x, 1) == 50.0
    assert round(c_elem.bounds.x - orig_c_x, 1) == 50.0


def test_mermaid_diagram_and_targeting():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    # 1. Create Mermaid Flowchart
    mermaid_code = """graph TD
    A[Start Evaluation] --> B{Discriminant Δ >= 0?}
    B -->|Yes| C[Real Roots]
    B -->|No| D[Complex Roots]"""

    m_res = reg.create_mermaid(mermaid_code, title="Root Classifier")
    assert m_res["success"] is True
    assert "mrmd-" in m_res["id"]
    elem = mem.get_element(m_res["id"])
    assert elem.type == "mermaid"
    assert elem.content["mermaid_code"] == mermaid_code

    # 2. Target a node or term inside the Mermaid diagram
    u_res = reg.underline_element(target_id=m_res["id"], target_text="Real Roots")
    assert u_res["success"] is True
    assert u_res["target_text"] == "Real Roots"

    # 3. Create diagram using mermaid_code parameter
    diag_res = reg.create_diagram(mermaid_code="sequenceDiagram\nAlice->>Bob: Hello\nBob-->>Alice: Hi", title="Handshake")
    assert diag_res["success"] is True
    assert "mrmd-" in diag_res["id"]
