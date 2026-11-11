"""Tests for MathCanvas Visual Chain of Thought (VCoT) and Geometric Construction tools."""

from whiteboard_agent.spatial_memory import SpatialMemory
from whiteboard_agent.tools import WhiteboardToolRegistry


def test_construct_triangle_and_points():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    res = reg.construct_geometry(
        figure_type="triangle",
        title="Triangle ABC",
    )
    assert res["success"] is True
    assert "geom-" in res["id"]
    pts = res["points"]
    assert "A" in pts and "B" in pts and "C" in pts


def test_add_auxiliary_altitude_and_median():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    geom = reg.construct_geometry(figure_type="triangle")
    gid = geom["id"]

    # Add altitude from A to BC
    alt_res = reg.add_auxiliary_line(
        geometry_id=gid,
        line_type="altitude",
        from_point="A",
        base_points=("B", "C"),
        label="H",
        color="#dc2626",
    )
    assert alt_res["success"] is True
    assert alt_res["line_type"] == "altitude"
    assert alt_res["label"] == "H"
    assert "aux-" in alt_res["id"]

    # Add median from A to BC
    med_res = reg.add_auxiliary_line(
        geometry_id=gid,
        line_type="median",
        from_point="A",
        base_points=("B", "C"),
        label="M",
        color="#2563eb",
    )
    assert med_res["success"] is True
    assert med_res["label"] == "M"


def test_mark_geometry_right_angle_and_ticks():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    geom = reg.construct_geometry(figure_type="triangle")
    gid = geom["id"]

    # Mark angle arc at A
    arc_res = reg.mark_geometry(
        geometry_id=gid,
        mark_type="angle_arc",
        vertex="A",
        arms=("B", "C"),
    )
    assert arc_res["success"] is True
    assert "mark-" in arc_res["id"]

    # Mark congruent ticks on segment AB
    tick_res = reg.mark_geometry(
        geometry_id=gid,
        mark_type="congruent_ticks",
        segment=("A", "B"),
        ticks=2,
    )
    assert tick_res["success"] is True


def test_execute_vcot_interleaved_step():
    mem = SpatialMemory()
    reg = WhiteboardToolRegistry(mem)

    step_res = reg.execute_vcot_step(
        thought="Let ABC be an equilateral triangle with base on the x-axis.",
        drawing_action="construct_geometry",
        drawing_args={"figure_type": "triangle", "title": "Equilateral Triangle ABC"},
    )
    assert step_res["success"] is True
    assert "thought_id" in step_res
    assert step_res["visual_result"]["success"] is True
