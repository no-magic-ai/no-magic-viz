"""
Scene: SSM Discretization
Script: microdiscretize.py
Description: Euler, ZOH, Trapezoidal — different stability, different inductive bias
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_GRID, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


class DiscretizeScene(NoMagicScene):
    title_text = "SSM Discretization"
    subtitle_text = "Euler, ZOH, Trapezoidal — different stability, different inductive bias"

    def animate(self):
        # === Step 1: Continuous-time SSM equation ===
        cont_label = Text("Continuous-time SSM", font_size=18, color=NM_PRIMARY, weight=BOLD)
        cont_label.move_to(UP * 3.0)
        self.play(Write(cont_label), run_time=0.5)

        cont_eq = MathTex(r"h'(t) = A \, h(t) + B \, x(t)", font_size=30, color=NM_GREEN)
        cont_eq.move_to(UP * 2.1)
        self.play(FadeIn(cont_eq), run_time=0.4)

        disc_note = Text(
            "To run on digital hardware, discretize with step size \u0394",
            font_size=14, color=NM_TEXT,
        )
        disc_note.move_to(UP * 1.3)
        self.play(FadeIn(disc_note), run_time=0.4)

        arrow_down = Arrow(UP * 0.9, UP * 0.3, color=NM_YELLOW, stroke_width=2, tip_length=0.12)
        disc_eq = MathTex(r"h_t = \bar{A} \, h_{t-1} + \bar{B} \, x_t", font_size=28, color=NM_YELLOW)
        disc_eq.move_to(DOWN * 0.1)
        self.play(GrowArrow(arrow_down), FadeIn(disc_eq), run_time=0.5)

        how_label = Text("How to compute A\u0304 and B\u0304?  Three choices:", font_size=14, color=NM_GRID)
        how_label.move_to(DOWN * 0.7)
        self.play(FadeIn(how_label), run_time=0.3)
        self.wait(0.8)

        # === Step 2: Three discretization formulas side by side ===
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)

        methods_label = Text("Discretization Methods", font_size=18, color=NM_PRIMARY, weight=BOLD)
        methods_label.move_to(UP * 3.0)
        self.play(Write(methods_label), run_time=0.4)

        # Euler
        euler_title = Text("Euler", font_size=16, color=NM_BLUE, weight=BOLD)
        euler_eq = MathTex(r"\bar{A} = I + \Delta A", font_size=24, color=NM_TEXT)
        euler_note = Text("First-order approx", font_size=11, color=NM_GRID)
        euler_group = VGroup(euler_title, euler_eq, euler_note).arrange(DOWN, buff=0.15)

        # ZOH
        zoh_title = Text("ZOH", font_size=16, color=NM_GREEN, weight=BOLD)
        zoh_eq = MathTex(r"\bar{A} = e^{\Delta A}", font_size=24, color=NM_TEXT)
        zoh_note = Text("Exact for constant x", font_size=11, color=NM_GRID)
        zoh_group = VGroup(zoh_title, zoh_eq, zoh_note).arrange(DOWN, buff=0.15)

        # Trapezoidal
        trap_title = Text("Trapezoidal", font_size=16, color=NM_YELLOW, weight=BOLD)
        trap_eq = MathTex(r"\bar{A} = e^{\Delta A}", font_size=24, color=NM_TEXT)
        trap_note = Text("Uses x_t AND x_{t-1}", font_size=11, color=NM_GRID)
        trap_group = VGroup(trap_title, trap_eq, trap_note).arrange(DOWN, buff=0.15)

        all_methods = VGroup(euler_group, zoh_group, trap_group).arrange(RIGHT, buff=1.2)
        all_methods.move_to(UP * 1.2)

        # Separator lines
        sep1 = Line(
            euler_group.get_right() + RIGHT * 0.5 + UP * 0.6,
            euler_group.get_right() + RIGHT * 0.5 + DOWN * 0.6,
            color=NM_GRID, stroke_width=1, stroke_opacity=0.4,
        )
        sep2 = Line(
            zoh_group.get_right() + RIGHT * 0.5 + UP * 0.6,
            zoh_group.get_right() + RIGHT * 0.5 + DOWN * 0.6,
            color=NM_GRID, stroke_width=1, stroke_opacity=0.4,
        )

        self.play(
            LaggedStart(
                FadeIn(euler_group, shift=UP * 0.1),
                FadeIn(zoh_group, shift=UP * 0.1),
                FadeIn(trap_group, shift=UP * 0.1),
                lag_ratio=0.15,
            ),
            Create(sep1), Create(sep2),
            run_time=1.0,
        )
        self.wait(0.8)

        # === Step 3: Stability comparison — |A_bar| vs increasing delta ===
        stability_label = Text("Stability: |\u0100| as \u0394 increases", font_size=16, color=NM_PRIMARY, weight=BOLD)
        stability_label.move_to(DOWN * 0.5)
        self.play(Write(stability_label), run_time=0.4)

        # Number line from 0 to 2.0 representing |A_bar|
        num_line = NumberLine(
            x_range=[0, 2.0, 0.5], length=5.0,
            color=NM_GRID, stroke_width=1.5,
            include_numbers=True, font_size=12,
            decimal_number_config={"color": NM_GRID},
        )
        num_line.move_to(DOWN * 1.5)

        # Stability boundary at 1.0
        stable_line = DashedLine(
            num_line.n2p(1.0) + UP * 0.5,
            num_line.n2p(1.0) + DOWN * 0.3,
            color=NM_PRIMARY, stroke_width=1.5,
        )
        stable_txt = Text("|A\u0304|=1", font_size=10, color=NM_PRIMARY)
        stable_txt.next_to(stable_line, UP, buff=0.05)

        self.play(Create(num_line), Create(stable_line), FadeIn(stable_txt), run_time=0.5)

        # Euler dot — starts stable, moves past 1.0 (diverges)
        euler_dot = Dot(num_line.n2p(0.6), radius=0.08, color=NM_BLUE)
        euler_lbl = Text("Euler", font_size=10, color=NM_BLUE)
        euler_lbl.next_to(euler_dot, UP, buff=0.12)

        # ZOH dot — stays below 1.0
        zoh_dot = Dot(num_line.n2p(0.5), radius=0.08, color=NM_GREEN)
        zoh_lbl = Text("ZOH", font_size=10, color=NM_GREEN)
        zoh_lbl.next_to(zoh_dot, DOWN, buff=0.12)

        # Trap dot — stays below 1.0
        trap_dot = Dot(num_line.n2p(0.55), radius=0.08, color=NM_YELLOW)
        trap_lbl = Text("Trap", font_size=10, color=NM_YELLOW)
        trap_lbl.next_to(trap_dot, DOWN, buff=0.25)

        self.play(
            FadeIn(euler_dot), FadeIn(euler_lbl),
            FadeIn(zoh_dot), FadeIn(zoh_lbl),
            FadeIn(trap_dot), FadeIn(trap_lbl),
            run_time=0.4,
        )

        # Animate increasing delta: Euler overshoots, others stay stable
        self.play(
            euler_dot.animate.move_to(num_line.n2p(1.4)),
            euler_lbl.animate.move_to(num_line.n2p(1.4) + UP * 0.2),
            zoh_dot.animate.move_to(num_line.n2p(0.85)),
            zoh_lbl.animate.move_to(num_line.n2p(0.85) + DOWN * 0.2),
            trap_dot.animate.move_to(num_line.n2p(0.9)),
            trap_lbl.animate.move_to(num_line.n2p(0.9) + DOWN * 0.35),
            run_time=1.2,
        )

        # Euler turns red (diverged)
        diverge_txt = Text("DIVERGES", font_size=10, color=NM_PRIMARY, weight=BOLD)
        diverge_txt.next_to(euler_dot, UP, buff=0.3)
        self.play(
            euler_dot.animate.set_color(NM_PRIMARY),
            FadeIn(diverge_txt),
            run_time=0.4,
        )
        self.wait(0.6)

        # === Step 4: Trapezoidal's implicit convolution ===
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)

        struct_label = Text("Trapezoidal: implicit short convolution", font_size=18, color=NM_PRIMARY, weight=BOLD)
        struct_label.move_to(UP * 2.8)
        self.play(Write(struct_label), run_time=0.5)

        # Show trapezoidal depends on x_t AND x_{t-1}
        trap_full = MathTex(
            r"h_t = \bar{A}\, h_{t-1} + \bar{B}_0\, x_t + \bar{B}_1\, x_{t-1}",
            font_size=26, color=NM_YELLOW,
        )
        trap_full.move_to(UP * 1.5)
        self.play(FadeIn(trap_full), run_time=0.5)

        # Show the two input dependency
        xt_box = RoundedRectangle(corner_radius=0.08, width=0.9, height=0.5, color=NM_GREEN, fill_opacity=0.2, stroke_width=1.5)
        xt_label = Text("x_t", font_size=14, color=NM_GREEN)
        xt_label.move_to(xt_box.get_center())
        xt_grp = VGroup(xt_box, xt_label)

        xt1_box = RoundedRectangle(corner_radius=0.08, width=0.9, height=0.5, color=NM_ORANGE, fill_opacity=0.2, stroke_width=1.5)
        xt1_label = Text("x_{t-1}", font_size=14, color=NM_ORANGE)
        xt1_label.move_to(xt1_box.get_center())
        xt1_grp = VGroup(xt1_box, xt1_label)

        ht_box = RoundedRectangle(corner_radius=0.1, width=1.0, height=0.6, color=NM_YELLOW, fill_opacity=0.2, stroke_width=1.5)
        ht_label = Text("h_t", font_size=14, color=NM_YELLOW)
        ht_label.move_to(ht_box.get_center())
        ht_grp = VGroup(ht_box, ht_label)

        inputs_grp = VGroup(xt1_grp, xt_grp).arrange(RIGHT, buff=0.8)
        inputs_grp.move_to(UP * 0.1)
        ht_grp.move_to(DOWN * 1.3)

        arr1 = Arrow(xt_grp.get_bottom(), ht_grp.get_top() + LEFT * 0.2, color=NM_GREEN, stroke_width=1.5, tip_length=0.1, buff=0.08)
        arr2 = Arrow(xt1_grp.get_bottom(), ht_grp.get_top() + RIGHT * 0.2, color=NM_ORANGE, stroke_width=1.5, tip_length=0.1, buff=0.08)

        self.play(
            FadeIn(xt_grp), FadeIn(xt1_grp), FadeIn(ht_grp),
            GrowArrow(arr1), GrowArrow(arr2),
            run_time=0.7,
        )

        conv_note = Text(
            "Size-2 convolution is built in — replaces Mamba-1/2's explicit short conv",
            font_size=13, color=NM_TEXT,
        )
        conv_note.move_to(DOWN * 2.3)

        fewer_note = Text(
            "Fewer parameters, same expressivity, better numerical stability",
            font_size=12, color=NM_GREEN,
        )
        fewer_note.move_to(DOWN * 2.8)

        self.play(FadeIn(conv_note), run_time=0.4)
        self.play(FadeIn(fewer_note), run_time=0.3)
        self.wait(1.2)

        # === Cleanup ===
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
