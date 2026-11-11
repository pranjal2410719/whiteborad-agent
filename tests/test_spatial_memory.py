"""Tests for SpatialMemory engine, BoundingBox math, collision avoidance, and empty space search."""

from whiteboard_agent.models import BoundingBox, WhiteboardElement
from whiteboard_agent.spatial_memory import SpatialMemory


def test_bounding_box_intersection():
    b1 = BoundingBox(x=0, y=0, width=100, height=100)
    b2 = BoundingBox(x=50, y=50, width=100, height=100)
    b3 = BoundingBox(x=200, y=200, width=50, height=50)

    assert b1.intersects(b2) is True
    assert b1.intersects(b3) is False
    assert b1.intersects(b3, margin=150) is True


def test_bounding_box_properties():
    b = BoundingBox(x=10, y=20, width=100, height=50)
    assert b.left == 10
    assert b.top == 20
    assert b.right == 110
    assert b.bottom == 70
    assert b.center_x == 60
    assert b.center_y == 45
    assert b.center == (60, 45)


def test_spatial_memory_element_crud():
    mem = SpatialMemory()
    el = WhiteboardElement(
        id="el-1",
        type="sticky_note",
        bounds=BoundingBox(x=0, y=0, width=100, height=80),
        title="Note 1",
        content="Hello",
    )
    mem.add_element(el)
    assert "el-1" in mem.elements
    assert mem.get_element("el-1").title == "Note 1"

    # Search by text
    results = mem.find_elements_by_text("hello")
    assert len(results) == 1
    assert results[0].id == "el-1"

    # Update
    mem.update_element_bounds("el-1", x=50, y=60)
    assert mem.get_element("el-1").bounds.x == 50

    # Delete
    mem.remove_element("el-1")
    assert "el-1" not in mem.elements


def test_empty_space_search_no_overlap():
    mem = SpatialMemory()

    # Add initial element
    e1 = WhiteboardElement(
        id="e1",
        type="sticky_note",
        bounds=BoundingBox(x=0, y=0, width=200, height=150),
    )
    mem.add_element(e1)

    # Ask for space for second element to the right
    box_right = mem.find_empty_space(width=150, height=100, anchor_id="e1", direction="right")
    assert box_right.left >= e1.bounds.right
    assert not box_right.intersects(e1.bounds, margin=10)

    # Ask for space for third element to the bottom
    box_bottom = mem.find_empty_space(width=150, height=100, anchor_id="e1", direction="bottom")
    assert box_bottom.top >= e1.bounds.bottom
    assert not box_bottom.intersects(e1.bounds, margin=10)


def test_multiple_elements_continuous_packing():
    mem = SpatialMemory()
    boxes = []

    for i in range(10):
        box = mem.find_empty_space(width=120, height=80)
        # Verify it does not collide with ANY previous box
        for prev in boxes:
            assert not box.intersects(prev, margin=5), f"Box {i} collided with previous box"
        elem = WhiteboardElement(id=f"el-{i}", type="sticky_note", bounds=box)
        mem.add_element(elem)
        boxes.append(box)

    assert len(mem.elements) == 10
