"""Tests for underline, circle, arrow, and SVG geometry helpers."""

from whiteboard_agent.geometry import (
    create_arrow_path,
    create_circle_path,
    create_underline_path,
)
from whiteboard_agent.models import BoundingBox


def test_create_underline_path():
    box = BoundingBox(x=100, y=100, width=200, height=80)
    data = create_underline_path(box, style="straight")

    assert "M" in data["svg_path"]
    assert data["start"][0] < box.left  # Starts slightly before
    assert data["end"][0] > box.right   # Ends slightly after
    assert data["start"][1] > box.bottom  # Sits below


def test_create_circle_path():
    box = BoundingBox(x=50, y=50, width=100, height=60)
    data = create_circle_path(box, padding=10, style="smooth")

    assert "a" in data["svg_path"]
    assert data["center"] == [100.0, 80.0]
    assert data["rx"] == 60.0  # 100/2 + 10
    assert data["ry"] == 40.0  # 60/2 + 10


def test_create_arrow_path():
    b1 = BoundingBox(x=0, y=0, width=100, height=50)
    b2 = BoundingBox(x=200, y=0, width=100, height=50)
    data = create_arrow_path(b1, b2, style="straight")

    assert "M" in data["svg_path"]
    assert data["start"][0] == 100.0  # Right edge of b1
    assert data["end"][0] == 200.0    # Left edge of b2


def test_calculate_sub_text_bounds():
    from whiteboard_agent.geometry import calculate_sub_text_bounds
    parent = BoundingBox(x=100, y=100, width=300, height=120)
    full_formula = "a² + b² = c²"

    # Target specific term 'c²'
    c_box = calculate_sub_text_bounds(parent, full_formula, "c²", font_size=30.0)
    assert c_box.left > parent.left
    assert c_box.width < parent.width
    assert c_box.right <= parent.right + 20

    # Target term 'a²'
    a_box = calculate_sub_text_bounds(parent, full_formula, "a²", font_size=30.0)
    assert a_box.left < c_box.left
