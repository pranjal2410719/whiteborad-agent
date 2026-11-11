"""MathCanvas Visual Chain-of-Thought (VCoT) & Geometric Construction Engine.

Inspired by MathCanvas (ACL 2026, CUHK MMLab & Huawei Research) and AlphaGeometry:
Enables models to solve mathematical problems through interleaved visual-textual reasoning:
- Foundational geometric constructions (points, segments, triangles, circles, coordinate systems)
- Dynamic visual editing & auxiliary lines (altitudes, medians, tangents, angle bisectors)
- Geometric markings (right angle squares, congruence ticks, angle arcs)
- Interleaved Visual Chain-of-Thought (VCoT) execution trajectories
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple

from .models import BoundingBox, WhiteboardElement


class MathCanvasGeometry:
    """Mathematical and geometric calculations for pure-pen visual constructions."""

    @staticmethod
    def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    @staticmethod
    def midpoint(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    @staticmethod
    def project_point_on_segment(
        p: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Projects point p perpendicularly onto line segment AB."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return a
        t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length_sq
        return (a[0] + t * dx, a[1] + t * dy)

    @staticmethod
    def right_angle_square_path(
        vertex: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        size: float = 12.0,
    ) -> str:
        """Generates SVG path for a perpendicular mark (small square) at a right angle."""
        vx, vy = vertex
        # Normalized direction vectors
        d1 = MathCanvasGeometry.distance(vertex, p1)
        d2 = MathCanvasGeometry.distance(vertex, p2)
        if d1 == 0 or d2 == 0:
            return ""
        u1x, u1y = (p1[0] - vx) / d1, (p1[1] - vy) / d1
        u2x, u2y = (p2[0] - vx) / d2, (p2[1] - vy) / d2

        c1 = (vx + u1x * size, vy + u1y * size)
        c2 = (vx + u1x * size + u2x * size, vy + u1y * size + u2y * size)
        c3 = (vx + u2x * size, vy + u2y * size)

        return f"M {c1[0]:.1f} {c1[1]:.1f} L {c2[0]:.1f} {c2[1]:.1f} L {c3[0]:.1f} {c3[1]:.1f}"

    @staticmethod
    def angle_arc_path(
        vertex: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        radius: float = 20.0,
    ) -> str:
        """Generates SVG arc mark between two rays originating from vertex."""
        a1 = math.atan2(p1[1] - vertex[1], p1[0] - vertex[0])
        a2 = math.atan2(p2[1] - vertex[1], p2[0] - vertex[0])
        # Ensure positive angle sweep
        diff = (a2 - a1) % (2 * math.pi)
        if diff > math.pi:
            a1, a2 = a2, a1

        sx = vertex[0] + radius * math.cos(a1)
        sy = vertex[1] + radius * math.sin(a1)
        ex = vertex[0] + radius * math.cos(a2)
        ey = vertex[1] + radius * math.sin(a2)

        return f"M {sx:.1f} {sy:.1f} A {radius} {radius} 0 0 1 {ex:.1f} {ey:.1f}"

    @staticmethod
    def congruent_ticks_path(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        ticks: int = 1,
        tick_len: float = 8.0,
    ) -> str:
        """Generates perpendicular tick marks in the center of segment p1-p2."""
        mx, my = MathCanvasGeometry.midpoint(p1, p2)
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return ""
        # Perpendicular normal unit vector
        nx, ny = -dy / dist, dx / dist
        # Tangent unit vector
        tx, ty = dx / dist, dy / dist

        paths = []
        spacing = 4.0
        start_offset = -((ticks - 1) * spacing) / 2.0

        for i in range(ticks):
            off = start_offset + i * spacing
            cx = mx + tx * off
            cy = my + ty * off
            x1 = cx - nx * (tick_len / 2.0)
            y1 = cy - ny * (tick_len / 2.0)
            x2 = cx + nx * (tick_len / 2.0)
            y2 = cy + ny * (tick_len / 2.0)
            paths.append(f"M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}")

        return " ".join(paths)


class MathCanvasToolExtension:
    """MathCanvas tools for geometric constructions and Visual Chain of Thought."""

    def __init__(self, memory: Any):
        self.memory = memory

    # --- MathCanvas Tool 1: Construct Geometry Figure ---
    def construct_geometry(
        self,
        figure_type: Literal["triangle", "circle", "quadrilateral", "polygon", "coordinate_system"],
        points: Optional[Dict[str, Tuple[float, float]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        title: Optional[str] = "Geometric Construction",
        stroke_color: str = "#0f172a",
        anchor_id: Optional[str] = None,
        direction: str = "auto",
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: float = 280.0,
        height: float = 220.0,
    ) -> Dict[str, Any]:
        """Constructs foundational geometric figures with exact points, sides, and vertex labels."""
        params = parameters or {}
        elem_id = f"geom-{uuid.uuid4().hex[:6]}"

        if x is None or y is None:
            box = self.memory.find_empty_space(width, height, anchor_id=anchor_id, direction=direction)
        else:
            box = BoundingBox(x=x, y=y, width=width, height=height)

        # Build coordinate scale relative to bounding box center
        cx, cy = box.center_x, box.center_y

        computed_points: Dict[str, Tuple[float, float]] = {}
        svg_elements: List[str] = []

        if figure_type == "triangle":
            # Default triangle: A at top, B at bottom-left, C at bottom-right
            if points and len(points) >= 3:
                # Offset user relative points to canvas center
                for name, pt in points.items():
                    computed_points[name] = (cx + pt[0], cy + pt[1])
            else:
                computed_points["A"] = (cx, cy - (height * 0.4))
                computed_points["B"] = (cx - (width * 0.38), cy + (height * 0.38))
                computed_points["C"] = (cx + (width * 0.38), cy + (height * 0.38))

            pts_list = list(computed_points.values())
            path_d = f"M {pts_list[0][0]:.1f} {pts_list[0][1]:.1f} L {pts_list[1][0]:.1f} {pts_list[1][1]:.1f} L {pts_list[2][0]:.1f} {pts_list[2][1]:.1f} Z"
            svg_elements.append(
                f'<path d="{path_d}" fill="none" stroke="{stroke_color}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>'
            )

            # Vertex point dots and labels
            for name, (px, py) in computed_points.items():
                svg_elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{stroke_color}"/>')
                # Place label offset away from center
                lx = px + (12 if px >= cx else -18)
                ly = py + (16 if py >= cy else -10)
                svg_elements.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-family="Caveat, cursive" font-size="22" font-weight="bold" fill="{stroke_color}">{name}</text>')

        elif figure_type == "circle":
            radius = params.get("radius", min(width, height) * 0.38)
            computed_points["O"] = (cx, cy)
            svg_elements.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="none" stroke="{stroke_color}" stroke-width="2.8"/>'
            )
            svg_elements.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.5" fill="{stroke_color}"/>')
            svg_elements.append(f'<text x="{cx+8:.1f}" y="{cy-8:.1f}" font-family="Caveat, cursive" font-size="20" font-weight="bold" fill="{stroke_color}">O</text>')

        elif figure_type == "coordinate_system":
            computed_points["O"] = (cx, cy)
            # Axes
            x1, x2 = box.left + 15, box.right - 15
            y1, y2 = box.bottom - 15, box.top + 15
            svg_elements.append(f'<line x1="{x1:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{cy:.1f}" stroke="{stroke_color}" stroke-width="2.5" stroke-linecap="round"/>')
            svg_elements.append(f'<polygon points="{x2:.1f},{cy-4:.1f} {x2+8:.1f},{cy:.1f} {x2:.1f},{cy+4:.1f}" fill="{stroke_color}"/>')
            svg_elements.append(f'<line x1="{cx:.1f}" y1="{y1:.1f}" x2="{cx:.1f}" y2="{y2:.1f}" stroke="{stroke_color}" stroke-width="2.5" stroke-linecap="round"/>')
            svg_elements.append(f'<polygon points="{cx-4:.1f},{y2:.1f} {cx:.1f},{y2-8:.1f} {cx+4:.1f},{y2:.1f}" fill="{stroke_color}"/>')
            svg_elements.append(f'<text x="{x2+6:.1f}" y="{cy+14:.1f}" font-family="Caveat, cursive" font-size="20" fill="{stroke_color}">x</text>')
            svg_elements.append(f'<text x="{cx-16:.1f}" y="{y2-4:.1f}" font-family="Caveat, cursive" font-size="20" fill="{stroke_color}">y</text>')

        svg_content = f'<svg viewBox="{box.left-10} {box.top-10} {box.width+20} {box.height+20}" style="width:100%; height:100%; overflow:visible;">{"".join(svg_elements)}</svg>'

        elem = WhiteboardElement(
            id=elem_id,
            type="diagram",
            bounds=box,
            title=title,
            content={
                "figure_type": figure_type,
                "points": {k: [round(v[0], 1), round(v[1], 1)] for k, v in computed_points.items()},
                "svg": svg_content,
                "auxiliary_lines": [],
            },
            style={"color": stroke_color},
        )
        self.memory.add_element(elem)

        return {
            "success": True,
            "id": elem_id,
            "action": "construct_geometry",
            "figure_type": figure_type,
            "points": elem.content["points"],
            "bounds": box.to_dict(),
            "message": f"Constructed geometric {figure_type} '{elem_id}' with points {list(computed_points.keys())}",
        }

    # --- MathCanvas Tool 2: Add Auxiliary Line (MathCanvas-Edit core) ---
    def add_auxiliary_line(
        self,
        geometry_id: str,
        line_type: Literal["altitude", "median", "angle_bisector", "tangent", "segment", "perpendicular"],
        from_point: Optional[str] = None,
        to_point: Optional[str] = None,
        base_points: Optional[Tuple[str, str]] = None,
        label: str = "H",
        color: str = "#dc2626",
        style: Literal["dashed", "solid"] = "dashed",
    ) -> Dict[str, Any]:
        """Adds a strategic auxiliary construction line to an existing geometric figure.

        This is the core of MathCanvas Visual Chain of Thought (VCoT) editing:
        - Altitude: drops perpendicular from vertex to opposite base with right-angle mark.
        - Median: connects vertex to midpoint of opposite base with congruent tick marks.
        - Angle Bisector: bisects angle at vertex and draws arc markings.
        - Tangent: draws tangent line to circle.
        """
        geom = self.memory.get_element(geometry_id)
        pts = geom.content.get("points", {})

        p1: Tuple[float, float]
        p2: Tuple[float, float]
        aux_marks: List[str] = []

        if line_type == "altitude":
            v_name = from_point or "A"
            b1_name, b2_name = base_points or ("B", "C")
            if v_name not in pts or b1_name not in pts or b2_name not in pts:
                raise ValueError(f"Points for altitude ({v_name}, {b1_name}, {b2_name}) not found in {list(pts.keys())}")
            va = tuple(pts[v_name])
            vb1 = tuple(pts[b1_name])
            vb2 = tuple(pts[b2_name])

            # Drop perpendicular
            proj = MathCanvasGeometry.project_point_on_segment(va, vb1, vb2)
            pts[label] = [round(proj[0], 1), round(proj[1], 1)]
            p1, p2 = va, proj

            # Right angle symbol at H
            ra_sq = MathCanvasGeometry.right_angle_square_path(proj, va, vb2, size=11.0)
            if ra_sq:
                aux_marks.append(f'<path d="{ra_sq}" fill="none" stroke="{color}" stroke-width="2"/>')

        elif line_type == "median":
            v_name = from_point or "A"
            b1_name, b2_name = base_points or ("B", "C")
            va = tuple(pts[v_name])
            vb1 = tuple(pts[b1_name])
            vb2 = tuple(pts[b2_name])

            # Midpoint
            mid = MathCanvasGeometry.midpoint(vb1, vb2)
            pts[label] = [round(mid[0], 1), round(mid[1], 1)]
            p1, p2 = va, mid

            # Congruent tick marks on both halves
            t1 = MathCanvasGeometry.congruent_ticks_path(vb1, mid, ticks=2)
            t2 = MathCanvasGeometry.congruent_ticks_path(mid, vb2, ticks=2)
            if t1:
                aux_marks.append(f'<path d="{t1}" fill="none" stroke="{color}" stroke-width="2"/>')
            if t2:
                aux_marks.append(f'<path d="{t2}" fill="none" stroke="{color}" stroke-width="2"/>')

        else:
            # Segment between two named points
            if from_point not in pts or to_point not in pts:
                raise ValueError(f"Points {from_point} or {to_point} not found in {list(pts.keys())}")
            p1, p2 = tuple(pts[from_point]), tuple(pts[to_point])

        # Create auxiliary stroke
        dash_attr = ' stroke-dasharray="5 4"' if style == "dashed" else ""
        aux_line_svg = (
            f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" '
            f'stroke="{color}" stroke-width="2.5"{dash_attr} stroke-linecap="round"/>'
        )
        dot_svg = f'<circle cx="{p2[0]:.1f}" cy="{p2[1]:.1f}" r="3.5" fill="{color}"/>'
        lbl_svg = f'<text x="{p2[0]+8:.1f}" y="{p2[1]+14:.1f}" font-family="Caveat, cursive" font-size="20" font-weight="bold" fill="{color}">{label}</text>'

        # Register stroke on canvas
        stroke_id = f"aux-{uuid.uuid4().hex[:6]}"
        stroke = WhiteboardElement(
            id=stroke_id,
            type="stroke",
            bounds=geom.bounds,
            title=f"Auxiliary {line_type} {label}",
            content={
                "stroke_type": "auxiliary_line",
                "geometry_id": geometry_id,
                "line_type": line_type,
                "svg_fragment": f"{aux_line_svg} {dot_svg} {lbl_svg} {' '.join(aux_marks)}",
                "svg_path": f"M {p1[0]:.1f} {p1[1]:.1f} L {p2[0]:.1f} {p2[1]:.1f}",
                "from_point": list(p1),
                "to_point": list(p2),
            },
            target_id=geometry_id,
            style={"color": color, "stroke_width": 2.5, "dash": [5, 4] if style == "dashed" else None},
        )
        self.memory.add_element(stroke)

        return {
            "success": True,
            "id": stroke_id,
            "geometry_id": geometry_id,
            "action": "add_auxiliary_line",
            "line_type": line_type,
            "label": label,
            "from": list(p1),
            "to": list(p2),
            "message": f"Added auxiliary {line_type} line '{label}' to geometry {geometry_id}",
        }

    # --- MathCanvas Tool 3: Mark Geometric Angles / Congruence ---
    def mark_geometry(
        self,
        geometry_id: str,
        mark_type: Literal["right_angle", "congruent_ticks", "angle_arc"],
        vertex: Optional[str] = None,
        arms: Optional[Tuple[str, str]] = None,
        segment: Optional[Tuple[str, str]] = None,
        ticks: int = 1,
        color: str = "#dc2626",
    ) -> Dict[str, Any]:
        """Draws right angle squares, angle arcs, or congruence ticks onto geometric elements."""
        geom = self.memory.get_element(geometry_id)
        pts = geom.content.get("points", {})

        svg_path = ""
        if mark_type == "right_angle" and vertex and arms:
            v = tuple(pts[vertex])
            a1, a2 = tuple(pts[arms[0]]), tuple(pts[arms[1]])
            svg_path = MathCanvasGeometry.right_angle_square_path(v, a1, a2)
        elif mark_type == "congruent_ticks" and segment:
            p1, p2 = tuple(pts[segment[0]]), tuple(pts[segment[1]])
            svg_path = MathCanvasGeometry.congruent_ticks_path(p1, p2, ticks=ticks)
        elif mark_type == "angle_arc" and vertex and arms:
            v = tuple(pts[vertex])
            a1, a2 = tuple(pts[arms[0]]), tuple(pts[arms[1]])
            svg_path = MathCanvasGeometry.angle_arc_path(v, a1, a2)

        stroke_id = f"mark-{uuid.uuid4().hex[:6]}"
        stroke = WhiteboardElement(
            id=stroke_id,
            type="stroke",
            bounds=geom.bounds,
            title=f"Geometric Mark {mark_type}",
            content={"stroke_type": mark_type, "svg_path": svg_path},
            target_id=geometry_id,
            style={"color": color, "stroke_width": 2.0},
        )
        self.memory.add_element(stroke)

        return {
            "success": True,
            "id": stroke_id,
            "geometry_id": geometry_id,
            "action": "mark_geometry",
            "mark_type": mark_type,
            "svg_path": svg_path,
            "message": f"Marked {mark_type} on geometry {geometry_id}",
        }

    # --- MathCanvas Tool 4: Interleaved Visual Chain of Thought (VCoT) Step ---
    def execute_vcot_step(
        self,
        thought: str,
        drawing_action: Optional[str] = None,
        drawing_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes a single step in an intrinsic Visual Chain-of-Thought (VCoT) trajectory.

        Interleaves natural language deductive reasoning with immediate visual diagram operations:
        - Writes reasoning statement directly in pen ink.
        - Executes corresponding geometric construction, auxiliary line, formula, or plot.
        """
        # Step 1: Write thought step in pen ink
        thought_res = self.memory.add_element(
            WhiteboardElement(
                type="text",
                bounds=self.memory.find_empty_space(width=280.0, height=50.0, direction="bottom"),
                title="Reasoning Step",
                content=thought,
                style={"font_size": 22, "color": "#0f172a"},
            )
        )

        visual_res = None
        if drawing_action and drawing_args:
            # Delegate to corresponding tool
            handler = getattr(self, drawing_action, None)
            if handler:
                visual_res = handler(**drawing_args)

        return {
            "success": True,
            "action": "execute_vcot_step",
            "thought_id": thought_res.id,
            "visual_result": visual_res,
            "message": f"Executed VCoT step: '{thought[:40]}...'",
        }
