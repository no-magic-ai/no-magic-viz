"""
Scene: Vector Search
Script: microvectorsearch.py
Description: Exact vs approximate nearest neighbors — brute force vs LSH buckets
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


class VectorSearchScene(NoMagicScene):
    title_text = "Vector Search"
    subtitle_text = "Exact vs approximate nearest neighbors"

    def animate(self):
        # === Step 1: Show points in 2D embedding space ===
        space_label = Text("Embedding Space", font_size=20, color=NM_TEXT, weight=BOLD)
        space_label.move_to(UP * 3.0)
        self.play(Write(space_label), run_time=0.4)

        # Data points (fixed positions for determinism)
        point_coords = [
            (-3.0, 1.5), (-2.2, 0.8), (-1.5, 2.0), (-0.8, 0.3),
            (0.5, 1.8), (1.2, 0.5), (2.0, 1.2), (2.8, 2.0),
            (-2.5, -0.5), (-1.0, -1.0), (0.3, -0.8), (1.5, -0.3),
            (2.5, -1.2), (-0.5, 1.0), (1.8, -0.8),
        ]

        dots = VGroup()
        for x, y in point_coords:
            dot = Dot(
                point=[x, y, 0], radius=0.08, color=NM_BLUE,
            )
            dot.set_fill(opacity=0.7)
            dots.add(dot)

        self.play(
            LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.03),
            run_time=0.8,
        )

        # Query point
        query = Dot(point=[0.8, 0.8, 0], radius=0.12, color=NM_PRIMARY)
        query.set_fill(opacity=0.9)
        q_label = Text("query", font_size=12, color=NM_PRIMARY)
        q_label.next_to(query, UP, buff=0.1)
        self.play(FadeIn(query, scale=1.5), FadeIn(q_label), run_time=0.5)
        self.wait(0.4)

        # === Step 2: Brute-force search — scan every point ===
        brute_label = Text("Brute Force: O(n) comparisons", font_size=16, color=NM_ORANGE, weight=BOLD)
        brute_label.move_to(DOWN * 2.5)
        self.play(Write(brute_label), run_time=0.4)

        # Animate scanning lines from query to each point
        scan_lines = VGroup()
        for dot in dots:
            line = Line(
                query.get_center(), dot.get_center(),
                stroke_width=1, color=NM_ORANGE, stroke_opacity=0.4,
            )
            scan_lines.add(line)

        self.play(
            LaggedStart(*[Create(l) for l in scan_lines], lag_ratio=0.04),
            run_time=1.2,
        )

        # Find nearest (index 5 = (1.2, 0.5) is close to query (0.8, 0.8))
        nearest_idx = 5
        nearest_circle = Circle(
            radius=0.2, color=NM_GREEN, stroke_width=2,
        )
        nearest_circle.move_to(dots[nearest_idx].get_center())
        self.play(Create(nearest_circle), run_time=0.4)
        self.wait(0.4)

        # Fade out brute force
        self.play(
            FadeOut(scan_lines), FadeOut(nearest_circle), FadeOut(brute_label),
            run_time=0.5,
        )

        # === Step 3: LSH — hash into buckets ===
        lsh_label = Text("LSH: Hash into buckets, search locally", font_size=16, color=NM_GREEN, weight=BOLD)
        lsh_label.move_to(DOWN * 2.5)
        self.play(Write(lsh_label), run_time=0.4)

        # Draw bucket boundaries (vertical + horizontal dividers)
        v_line = DashedLine(
            UP * 2.5, DOWN * 1.8,
            color=NM_YELLOW, stroke_width=1.5, dash_length=0.1,
        )
        h_line = DashedLine(
            LEFT * 4 + UP * 0.3, RIGHT * 4 + UP * 0.3,
            color=NM_YELLOW, stroke_width=1.5, dash_length=0.1,
        )

        bucket_labels = VGroup(
            Text("B0", font_size=14, color=NM_YELLOW).move_to(LEFT * 2.5 + UP * 1.8),
            Text("B1", font_size=14, color=NM_YELLOW).move_to(RIGHT * 2.0 + UP * 1.8),
            Text("B2", font_size=14, color=NM_YELLOW).move_to(LEFT * 2.5 + DOWN * 0.8),
            Text("B3", font_size=14, color=NM_YELLOW).move_to(RIGHT * 2.0 + DOWN * 0.8),
        )

        self.play(Create(v_line), Create(h_line), run_time=0.6)
        self.play(FadeIn(bucket_labels), run_time=0.4)

        # Highlight query's bucket (B1: x>0, y>0.3)
        bucket_rect = Rectangle(
            width=4.0, height=2.2,
            color=NM_GREEN, fill_opacity=0.1, stroke_width=2,
        )
        bucket_rect.move_to(RIGHT * 2.0 + UP * 1.4)
        self.play(Create(bucket_rect), run_time=0.5)

        # Only scan points in the bucket
        bucket_points = [i for i, (x, y) in enumerate(point_coords) if x > 0 and y > 0.3]
        bucket_lines = VGroup()
        for idx in bucket_points:
            line = Line(
                query.get_center(), dots[idx].get_center(),
                stroke_width=1.5, color=NM_GREEN, stroke_opacity=0.6,
            )
            bucket_lines.add(line)

        self.play(
            LaggedStart(*[Create(l) for l in bucket_lines], lag_ratio=0.08),
            run_time=0.6,
        )

        nearest_circle2 = Circle(radius=0.2, color=NM_GREEN, stroke_width=2.5)
        nearest_circle2.move_to(dots[nearest_idx].get_center())
        self.play(Create(nearest_circle2), run_time=0.4)
        self.wait(0.4)

        # === Step 4: Tradeoff summary ===
        self.play(
            FadeOut(bucket_lines), FadeOut(bucket_rect),
            FadeOut(v_line), FadeOut(h_line), FadeOut(bucket_labels),
            FadeOut(lsh_label), FadeOut(nearest_circle2),
            run_time=0.5,
        )

        tradeoff = VGroup(
            Text("Exact:       O(n) \u2014 always correct", font_size=14, color=NM_ORANGE),
            Text("Approximate: O(1) \u2014 fast, might miss", font_size=14, color=NM_GREEN),
            Text("LSH trades accuracy for speed", font_size=16, color=NM_YELLOW, weight=BOLD),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        tradeoff.move_to(DOWN * 2.5)

        self.play(
            LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in tradeoff], lag_ratio=0.15),
            run_time=0.8,
        )
        self.wait(1.6)

        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
