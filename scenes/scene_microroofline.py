"""
Scene: Roofline Model
Script: microroofline.py
Description: Why more FLOPs can be faster — SISO vs MIMO on real hardware
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_GREEN, NM_GRID, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


class RooflineScene(NoMagicScene):
    title_text = "Roofline Model"
    subtitle_text = "Why more FLOPs can be faster — SISO vs MIMO on real hardware"

    def animate(self):
        # === Step 1: Draw the roofline diagram ===
        roofline_label = Text("Roofline Model", font_size=18, color=NM_PRIMARY, weight=BOLD)
        roofline_label.move_to(UP * 3.2)
        self.play(Write(roofline_label), run_time=0.4)

        # Axes
        axes = Axes(
            x_range=[0, 6, 1], y_range=[0, 5, 1],
            x_length=5.5, y_length=3.5,
            axis_config={"color": NM_GRID, "stroke_width": 1.5, "include_ticks": False},
        )
        axes.move_to(DOWN * 0.3 + LEFT * 0.5)

        x_label = Text("Arithmetic Intensity (FLOPs/byte)", font_size=11, color=NM_TEXT)
        x_label.next_to(axes.x_axis, DOWN, buff=0.2)
        y_label = Text("Throughput (FLOP/s)", font_size=11, color=NM_TEXT)
        y_label.next_to(axes.y_axis, UP, buff=0.15).shift(LEFT * 0.3)

        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), run_time=0.6)

        # Roofline: bandwidth slope then flat compute ceiling
        # Ridge point at AI=3, throughput=4
        ridge_ai = 3.0
        peak_throughput = 4.0
        bw_slope = peak_throughput / ridge_ai  # slope in data coords

        # Bandwidth-bound segment: (0,0) to (ridge_ai, peak_throughput)
        bw_line = Line(
            axes.c2p(0.2, 0.2 * bw_slope),
            axes.c2p(ridge_ai, peak_throughput),
            color=NM_YELLOW, stroke_width=2.5,
        )
        # Compute-bound segment: (ridge_ai, peak_throughput) to (6, peak_throughput)
        compute_line = Line(
            axes.c2p(ridge_ai, peak_throughput),
            axes.c2p(6, peak_throughput),
            color=NM_GREEN, stroke_width=2.5,
        )

        self.play(Create(bw_line), run_time=0.5)
        self.play(Create(compute_line), run_time=0.4)

        # Region labels
        mem_label = Text("Memory-\nbound", font_size=10, color=NM_YELLOW)
        mem_label.move_to(axes.c2p(1.0, 3.0))
        comp_label = Text("Compute-\nbound", font_size=10, color=NM_GREEN)
        comp_label.move_to(axes.c2p(4.8, 3.0))

        # Ridge point marker
        ridge_dot = Dot(axes.c2p(ridge_ai, peak_throughput), radius=0.06, color=NM_PRIMARY)
        ridge_txt = Text("ridge point", font_size=9, color=NM_PRIMARY)
        ridge_txt.next_to(ridge_dot, UP + RIGHT, buff=0.1)

        self.play(
            FadeIn(mem_label), FadeIn(comp_label),
            FadeIn(ridge_dot), FadeIn(ridge_txt),
            run_time=0.5,
        )
        self.wait(0.6)

        # === Step 2: Place SISO marker — low AI, memory-bound ===
        siso_ai = 0.8
        siso_tp = siso_ai * bw_slope
        siso_dot = Dot(axes.c2p(siso_ai, siso_tp), radius=0.1, color=NM_ORANGE)
        siso_label = Text("SISO", font_size=12, color=NM_ORANGE, weight=BOLD)
        siso_label.next_to(siso_dot, DOWN + RIGHT, buff=0.1)

        siso_info = Text("SISO: outer product, AI \u2248 2", font_size=13, color=NM_ORANGE)
        siso_info.move_to(DOWN * 2.8 + LEFT * 0.5)

        siso_note = Text("Deep in memory-bound territory — GPU ALUs idle", font_size=11, color=NM_GRID)
        siso_note.move_to(DOWN * 3.2 + LEFT * 0.5)

        self.play(FadeIn(siso_dot, scale=1.5), FadeIn(siso_label), run_time=0.5)
        self.play(FadeIn(siso_info), FadeIn(siso_note), run_time=0.4)
        self.wait(0.6)

        # === Step 3: Animate SISO moving right to become MIMO ===
        self.play(FadeOut(siso_info), FadeOut(siso_note), run_time=0.3)

        mimo_ai = 4.0
        mimo_tp = peak_throughput  # at the compute ceiling
        mimo_dot = Dot(axes.c2p(mimo_ai, mimo_tp), radius=0.1, color=NM_GREEN)

        # Trace path along the roofline
        trace_path = VMobject(color=NM_ORANGE, stroke_width=1.5, stroke_opacity=0.5)
        trace_points = []
        steps = 20
        for i in range(steps + 1):
            ai = siso_ai + (mimo_ai - siso_ai) * i / steps
            tp = min(ai * bw_slope, peak_throughput)
            trace_points.append(axes.c2p(ai, tp))
        trace_path.set_points_as_corners(trace_points)

        mimo_label = Text("MIMO", font_size=12, color=NM_GREEN, weight=BOLD)
        mimo_label.next_to(mimo_dot, UP + RIGHT, buff=0.1)

        mimo_info = Text("MIMO: matmul rank-r, AI \u2248 2r", font_size=13, color=NM_GREEN)
        mimo_info.move_to(DOWN * 2.8 + LEFT * 0.5)

        moving_txt = Text("More FLOPs, but higher utilization \u2192 faster wall-clock", font_size=11, color=NM_YELLOW)
        moving_txt.move_to(DOWN * 3.2 + LEFT * 0.5)

        self.play(
            Create(trace_path),
            siso_dot.animate.move_to(axes.c2p(mimo_ai, mimo_tp)).set_color(NM_GREEN),
            FadeOut(siso_label),
            run_time=1.5,
        )
        self.play(FadeIn(mimo_label), FadeIn(mimo_info), FadeIn(moving_txt), run_time=0.5)
        self.wait(0.6)

        # === Step 4: Hardware utilization comparison ===
        self.play(FadeOut(mimo_info), FadeOut(moving_txt), run_time=0.3)

        util_label = Text("GPU Compute Utilization", font_size=14, color=NM_TEXT, weight=BOLD)
        util_label.move_to(DOWN * 2.5 + RIGHT * 3.0)

        # SISO bar: <1%
        siso_bar_bg = Rectangle(width=2.0, height=0.3, color=NM_GRID, fill_opacity=0.15, stroke_width=1)
        siso_bar_fg = Rectangle(width=0.04, height=0.3, color=NM_ORANGE, fill_opacity=0.7, stroke_width=0)
        siso_bar_bg.move_to(DOWN * 3.0 + RIGHT * 3.3)
        siso_bar_fg.align_to(siso_bar_bg, LEFT)
        siso_pct = Text("SISO: <1%", font_size=10, color=NM_ORANGE)
        siso_pct.next_to(siso_bar_bg, LEFT, buff=0.15)

        # MIMO bar: ~60%
        mimo_bar_bg = Rectangle(width=2.0, height=0.3, color=NM_GRID, fill_opacity=0.15, stroke_width=1)
        mimo_bar_fg = Rectangle(width=1.2, height=0.3, color=NM_GREEN, fill_opacity=0.7, stroke_width=0)
        mimo_bar_bg.move_to(DOWN * 3.5 + RIGHT * 3.3)
        mimo_bar_fg.align_to(mimo_bar_bg, LEFT)
        mimo_pct = Text("MIMO: ~60%", font_size=10, color=NM_GREEN)
        mimo_pct.next_to(mimo_bar_bg, LEFT, buff=0.15)

        self.play(
            FadeIn(util_label),
            FadeIn(siso_bar_bg), GrowFromEdge(siso_bar_fg, LEFT), FadeIn(siso_pct),
            run_time=0.5,
        )
        self.play(
            FadeIn(mimo_bar_bg), GrowFromEdge(mimo_bar_fg, LEFT), FadeIn(mimo_pct),
            run_time=0.5,
        )

        takeaway = Text(
            "Mamba-3 MIMO: 8\u00d7 more FLOPs, 4\u00d7 faster on GPU",
            font_size=13, color=NM_YELLOW, weight=BOLD,
        )
        takeaway.move_to(DOWN * 2.0 + RIGHT * 3.0)
        self.play(FadeIn(takeaway), run_time=0.4)
        self.wait(1.2)

        # === Cleanup ===
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
