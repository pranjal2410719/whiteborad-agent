"""Geometry helpers for strokes, underlines, circles, arrows, and SVG paths."""

from __future__ import annotations

import math
from typing import Any, Dict, Literal

from .models import BoundingBox


def create_underline_path(
    box: BoundingBox,
    offset_y: float = 6.0,
    overflow_x: float = 8.0,
    style: Literal["straight", "wavy", "handdrawn"] = "handdrawn",
) -> Dict[str, Any]:
    """Computes start, end, and SVG path for an underline directly beneath an element."""
    x1 = box.left - overflow_x
    x2 = box.right + overflow_x
    y = box.bottom + offset_y

    if style == "straight":
        d = f"M {x1:.1f} {y:.1f} L {x2:.1f} {y:.1f}"
        points = [[x1, y], [x2, y]]
    elif style == "wavy":
        mid = (x1 + x2) / 2.0
        d = f"M {x1:.1f} {y:.1f} Q {(x1+mid)/2:.1f} {y+3:.1f} {mid:.1f} {y:.1f} T {x2:.1f} {y:.1f}"
        points = [[x1, y], [(x1+mid)/2, y+3], [mid, y], [(mid+x2)/2, y-3], [x2, y]]
    else:  # handdrawn natural slight curve
        mid_x = (x1 + x2) / 2.0
        mid_y = y + 2.5
        d = f"M {x1:.1f} {y:.1f} Q {mid_x:.1f} {mid_y:.1f} {x2:.1f} {y:.1f}"
        points = [[x1, y], [mid_x, mid_y], [x2, y]]

    return {
        "svg_path": d,
        "points": points,
        "start": [x1, y],
        "end": [x2, y],
        "bounds": BoundingBox(
            x=min(x1, x2),
            y=y - 4,
            width=abs(x2 - x1),
            height=12,
        ).to_dict(),
    }


def create_circle_path(
    box: BoundingBox,
    padding: float = 12.0,
    style: Literal["smooth", "handdrawn"] = "handdrawn",
) -> Dict[str, Any]:
    """Generates an organic or smooth circle/oval enclosing an element."""
    cx = box.center_x
    cy = box.center_y
    rx = (box.width / 2.0) + padding
    ry = (box.height / 2.0) + padding

    if style == "smooth":
        # Pure ellipse SVG path
        d = (
            f"M {cx - rx:.1f} {cy:.1f} "
            f"a {rx:.1f} {ry:.1f} 0 1 0 {rx * 2:.1f} 0 "
            f"a {rx:.1f} {ry:.1f} 0 1 0 {-rx * 2:.1f} 0"
        )
    else:
        # Hand-drawn whiteboard style with slight overlapping start & end
        # 4 cubic Bezier segments around the ellipse with natural jitter
        p0 = (cx - rx, cy + 2)
        c0 = (cx - rx, cy - ry * 0.55)
        c1 = (cx - rx * 0.55, cy - ry)
        p1 = (cx + 2, cy - ry)

        c2 = (cx + rx * 0.55, cy - ry)
        c3 = (cx + rx, cy - ry * 0.55)
        p2 = (cx + rx, cy)

        c4 = (cx + rx, cy + ry * 0.55)
        c5 = (cx + rx * 0.55, cy + ry)
        p3 = (cx - 1, cy + ry)

        # slight overshoot to mimic real pen closing loop
        c6 = (cx - rx * 0.6, cy + ry)
        c7 = (cx - rx - 2, cy + ry * 0.45)
        p4 = (cx - rx + 4, cy - 4)

        d = (
            f"M {p0[0]:.1f} {p0[1]:.1f} "
            f"C {c0[0]:.1f} {c0[1]:.1f}, {c1[0]:.1f} {c1[1]:.1f}, {p1[0]:.1f} {p1[1]:.1f} "
            f"C {c2[0]:.1f} {c2[1]:.1f}, {c3[0]:.1f} {c3[1]:.1f}, {p2[0]:.1f} {p2[1]:.1f} "
            f"C {c4[0]:.1f} {c4[1]:.1f}, {c5[0]:.1f} {c5[1]:.1f}, {p3[0]:.1f} {p3[1]:.1f} "
            f"C {c6[0]:.1f} {c6[1]:.1f}, {c7[0]:.1f} {c7[1]:.1f}, {p4[0]:.1f} {p4[1]:.1f}"
        )

    return {
        "svg_path": d,
        "center": [cx, cy],
        "rx": rx,
        "ry": ry,
        "bounds": BoundingBox(
            x=cx - rx - 4,
            y=cy - ry - 4,
            width=(rx * 2) + 8,
            height=(ry * 2) + 8,
        ).to_dict(),
    }


def create_arrow_path(
    from_box: BoundingBox,
    to_box: BoundingBox,
    style: Literal["straight", "curved"] = "curved",
) -> Dict[str, Any]:
    """Calculates connection points and SVG arrow path between two boxes."""
    # Find centers
    c1x, c1y = from_box.center
    c2x, c2y = to_box.center

    # Determine relative positioning
    dx = c2x - c1x
    dy = c2y - c1y

    # Select attachment points on boundaries
    if abs(dx) > abs(dy):
        # Horizontal flow
        if dx > 0:
            start = (from_box.right, c1y)
            end = (to_box.left, c2y)
        else:
            start = (from_box.left, c1y)
            end = (to_box.right, c2y)
    else:
        # Vertical flow
        if dy > 0:
            start = (c1x, from_box.bottom)
            end = (c2x, to_box.top)
        else:
            start = (c1x, from_box.top)
            end = (c2x, to_box.bottom)

    sx, sy = start
    ex, ey = end

    if style == "straight":
        d = f"M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}"
    else:
        # Smooth bezier curve
        cx1 = sx + (ex - sx) * 0.5
        cy1 = sy
        cx2 = sx + (ex - sx) * 0.5
        cy2 = ey
        d = f"M {sx:.1f} {sy:.1f} C {cx1:.1f} {cy1:.1f}, {cx2:.1f} {cy2:.1f}, {ex:.1f} {ey:.1f}"

    # Arrowhead calculation
    angle = math.atan2(ey - sy, ex - sx)
    arrow_size = 10.0
    a1_x = ex - arrow_size * math.cos(angle - math.pi / 6)
    a1_y = ey - arrow_size * math.sin(angle - math.pi / 6)
    a2_x = ex - arrow_size * math.cos(angle + math.pi / 6)
    a2_y = ey - arrow_size * math.sin(angle + math.pi / 6)
    arrowhead_path = f"M {a1_x:.1f} {a1_y:.1f} L {ex:.1f} {ey:.1f} L {a2_x:.1f} {a2_y:.1f}"

    min_x = min(sx, ex, a1_x, a2_x) - 5
    min_y = min(sy, ey, a1_y, a2_y) - 5
    max_x = max(sx, ex, a1_x, a2_x) + 5
    max_y = max(sy, ey, a1_y, a2_y) + 5

    return {
        "svg_path": f"{d} {arrowhead_path}",
        "line_path": d,
        "arrowhead_path": arrowhead_path,
        "start": [sx, sy],
        "end": [ex, ey],
        "bounds": BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y,
        ).to_dict(),
    }


def calculate_sub_text_bounds(
    parent_box: BoundingBox,
    full_text: str,
    target_text: str,
    font_size: float = 24.0,
    padding_x: float = 8.0,
    padding_y: float = 8.0,
) -> BoundingBox:
    """Calculates the exact 2D bounding box of a specific word or mathematical symbol inside an element."""
    if not target_text or not full_text:
        return parent_box

    # Case-insensitive fallback
    start_idx = full_text.find(target_text)
    if start_idx == -1:
        start_idx = full_text.lower().find(target_text.lower())
    if start_idx == -1:
        return parent_box

    before = full_text[:start_idx]
    lines = before.split("\n")
    line_idx = len(lines) - 1
    char_str = lines[-1]

    # Typography character width estimation for natural whiteboard markers
    def estimate_width(s: str, base_fs: float) -> float:
        total = 0.0
        for ch in s:
            if ch in "ijl|!.,:;' ":
                total += base_fs * 0.28
            elif ch in "mwMW_@%&":
                total += base_fs * 0.85
            elif ch in "ABCDEFGHJKLMNOPQRSTUVXYZ":
                total += base_fs * 0.65
            elif ch in "²³⁴⁰¹⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾":
                total += base_fs * 0.45
            else:
                total += base_fs * 0.52
        return total

    offset_x = estimate_width(char_str, font_size)
    word_width = max(14.0, estimate_width(target_text, font_size))
    line_height = font_size * 1.35

    x = parent_box.left + padding_x + offset_x
    y = parent_box.top + padding_y + (line_idx * line_height)
    height = font_size * 1.25

    return BoundingBox(
        x=round(x, 1),
        y=round(y, 1),
        width=round(word_width, 1),
        height=round(height, 1),
    )

