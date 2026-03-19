"""
Scene: Complex SSM Equivalence
Script: microcomplexssm.py
Description: Complex eigenvalues = real-valued RoPE — same rotation, same result
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import math

from base import NM_BLUE, NM_GREEN, NM_GRID, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


class ComplexSSMScene(NoMagicScene):
    title_text = "Complex SSM Equivalence"
    subtitle_text = "Complex eigenvalues = real-valued RoPE — same rotation, same result"

    def animate(self):
        # === Step 1: Real-only SSM — decay only ===
        real_label = Text("Real eigenvalue: decay only", font_size=18, color=NM_PRIMARY, weight=BOLD)
        real_label.move_to(UP * 3.0)
        self.play(Write(real_label), run_time=0.5)

        real_eq = Text("h_t = a · h_{t-1}    (a = 0.8)", font_size=16, color=NM_GREEN)
        real_eq.move_to(UP * 2.3)
        self.play(FadeIn(real_eq), run_time=0.4)

        # Show a state vector shrinking over 4 steps
        decay_dots = VGroup()
        decay_labels = VGroup()
        x_start, y_pos = -3.0, 0.5
        magnitude = 2.0
        a = 0.8
        for i in range(5):
            h = magnitude * (a ** i)
            bar = Rectangle(
                width=0.4, height=h,
                color=NM_BLUE, fill_opacity=0.4, stroke_width=1.5,
            )
            bar.move_to([x_start + i * 1.5, y_pos - 1.0 + h / 2, 0])
            t_label = Text(f"t={i}", font_size=12, color=NM_TEXT)
            t_label.next_to(bar, DOWN, buff=0.1)
            val_label = Text(f"|h|={h:.2f}", font_size=10, color=NM_BLUE)
            val_label.next_to(bar, UP, buff=0.05)
            decay_dots.add(VGroup(bar, val_label))
            decay_labels.add(t_label)

        self.play(
            LaggedStart(*[FadeIn(d, shift=UP * 0.1) for d in decay_dots], lag_ratio=0.15),
            LaggedStart(*[FadeIn(l) for l in decay_labels], lag_ratio=0.15),
            run_time=1.2,
        )

        note = Text("Shrinks monotonically — cannot rotate or oscillate", font_size=13, color=NM_GRID)
        note.move_to(DOWN * 2.2)
        self.play(FadeIn(note), run_time=0.3)
        self.wait(0.8)

        # === Step 2: Complex SSM — rotation + decay ===
        self.play(
            *[FadeOut(m) for m in [real_label, real_eq, decay_dots, decay_labels, note]],
            run_time=0.5,
        )

        complex_label = Text("Complex eigenvalue: rotation + decay", font_size=18, color=NM_PRIMARY, weight=BOLD)
        complex_label.move_to(UP * 3.0)
        self.play(Write(complex_label), run_time=0.5)

        complex_eq = MathTex(r"h_t = r \cdot e^{i\theta} \cdot h_{t-1}", font_size=32, color=NM_GREEN)
        complex_eq.move_to(UP * 2.3)
        self.play(FadeIn(complex_eq), run_time=0.4)

        # Small coordinate plane with rotating+shrinking point
        axes = Axes(
            x_range=[-1.6, 1.6, 0.5], y_range=[-1.6, 1.6, 0.5],
            x_length=3.5, y_length=3.5,
            axis_config={"color": NM_GRID, "stroke_width": 1},
        )
        axes.move_to(DOWN * 0.3)
        ax_labels = VGroup(
            Text("Re", font_size=11, color=NM_GRID).next_to(axes.x_axis, RIGHT, buff=0.1),
            Text("Im", font_size=11, color=NM_GRID).next_to(axes.y_axis, UP, buff=0.1),
        )
        self.play(Create(axes), FadeIn(ax_labels), run_time=0.5)

        # Trace the spiral: r=0.85, theta=pi/3 per step
        r_val, theta = 0.85, math.pi / 3
        trail_points = []
        radius = 1.3
        for i in range(7):
            mag = radius * (r_val ** i)
            angle = theta * i
            x = mag * math.cos(angle)
            y = mag * math.sin(angle)
            trail_points.append(axes.c2p(x, y))

        # Animate point stepping through the spiral
        dot = Dot(trail_points[0], radius=0.08, color=NM_YELLOW)
        self.play(FadeIn(dot), run_time=0.3)

        trail_lines = VGroup()
        for i in range(1, len(trail_points)):
            line = Line(trail_points[i - 1], trail_points[i], color=NM_ORANGE, stroke_width=1.5, stroke_opacity=0.6)
            new_dot = Dot(trail_points[i], radius=0.06, color=NM_YELLOW)
            trail_lines.add(line)
            self.play(
                Create(line),
                dot.animate.move_to(trail_points[i]),
                FadeIn(new_dot),
                run_time=0.3,
            )

        spiral_note = Text("State spirals inward — encodes position via phase", font_size=13, color=NM_YELLOW)
        spiral_note.move_to(DOWN * 2.8)
        self.play(FadeIn(spiral_note), run_time=0.3)
        self.wait(0.8)

        # === Step 3: Equivalence — complex multiply = 2x2 rotation matrix ===
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)

        equiv_label = Text("Equivalence: complex multiply = rotation matrix", font_size=18, color=NM_PRIMARY, weight=BOLD)
        equiv_label.move_to(UP * 2.8)
        self.play(Write(equiv_label), run_time=0.5)

        rot_matrix = MathTex(
            r"R(\theta) = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix}",
            font_size=30, color=NM_GREEN,
        )
        rot_matrix.move_to(LEFT * 2.0 + UP * 1.0)

        equiv_arrow = Arrow(LEFT * 0.2 + UP * 1.0, RIGHT * 1.3 + UP * 1.0, color=NM_YELLOW, stroke_width=2, tip_length=0.15)

        eitheta = MathTex(r"= e^{i\theta}", font_size=34, color=NM_YELLOW)
        eitheta.move_to(RIGHT * 2.2 + UP * 1.0)

        self.play(FadeIn(rot_matrix), run_time=0.5)
        self.play(GrowArrow(equiv_arrow), FadeIn(eitheta), run_time=0.5)

        impl_note = Text(
            "No complex arithmetic needed — 2x2 matmul on real pairs (same as RoPE)",
            font_size=14, color=NM_TEXT,
        )
        impl_note.move_to(DOWN * 0.2)
        self.play(FadeIn(impl_note), run_time=0.4)
        self.wait(0.8)

        # === Step 4: Parity task results ===
        result_label = Text("Parity task accuracy", font_size=16, color=NM_TEXT, weight=BOLD)
        result_label.move_to(DOWN * 1.2)
        self.play(FadeIn(result_label), run_time=0.3)

        # Real-only: ~50%, Complex/RoPE: ~95%
        bar_width = 2.5
        real_bar = Rectangle(width=bar_width * 0.5, height=0.35, color=NM_PRIMARY, fill_opacity=0.5, stroke_width=1.5)
        complex_bar = Rectangle(width=bar_width * 0.95, height=0.35, color=NM_GREEN, fill_opacity=0.5, stroke_width=1.5)
        rope_bar = Rectangle(width=bar_width * 0.93, height=0.35, color=NM_YELLOW, fill_opacity=0.5, stroke_width=1.5)

        bars = VGroup(real_bar, complex_bar, rope_bar).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        bars.move_to(DOWN * 2.2 + RIGHT * 0.3)

        real_txt = Text("Real-only   ~50%", font_size=12, color=NM_PRIMARY)
        complex_txt = Text("Complex      ~95%", font_size=12, color=NM_GREEN)
        rope_txt = Text("RoPE          ~93%", font_size=12, color=NM_YELLOW)

        for txt, bar in zip([real_txt, complex_txt, rope_txt], [real_bar, complex_bar, rope_bar]):
            txt.next_to(bar, LEFT, buff=0.2)

        self.play(
            LaggedStart(
                AnimationGroup(GrowFromEdge(real_bar, LEFT), FadeIn(real_txt)),
                AnimationGroup(GrowFromEdge(complex_bar, LEFT), FadeIn(complex_txt)),
                AnimationGroup(GrowFromEdge(rope_bar, LEFT), FadeIn(rope_txt)),
                lag_ratio=0.2,
            ),
            run_time=1.0,
        )

        verdict = Text("Real eigenvalues cannot solve parity — rotation is essential", font_size=13, color=NM_ORANGE)
        verdict.move_to(DOWN * 3.3)
        self.play(FadeIn(verdict), run_time=0.4)
        self.wait(1.2)

        # === Cleanup ===
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
