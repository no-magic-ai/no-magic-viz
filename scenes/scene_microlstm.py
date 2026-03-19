"""
Scene: LSTM — Long Short-Term Memory
Script: microlstm.py
Description: Four gates controlling the information highway — forget, input, cell state, output
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_ORANGE, NM_PRIMARY, NM_YELLOW, NoMagicScene
from manim import *


def make_gate_box(label, color, width=0.9, height=0.5):
    """Create a gate box with sigma symbol and label."""
    box = RoundedRectangle(
        corner_radius=0.08, width=width, height=height,
        color=color, fill_opacity=0.25, stroke_width=1.5,
    )
    text = Text(label, font_size=13, color=color, weight=BOLD)
    text.move_to(box.get_center())
    return VGroup(box, text)


class LSTMScene(NoMagicScene):
    title_text = "LSTM: Long Short-Term Memory"
    subtitle_text = "Four gates controlling the information highway"

    def animate(self):
        # === Step 1: Show the cell state conveyor belt ===
        cell_label = Text("Cell State (conveyor belt)", font_size=18, color=NM_GREEN, weight=BOLD)
        cell_label.move_to(UP * 3.0)

        cell_line = Arrow(
            LEFT * 5.5 + UP * 2.2, RIGHT * 5.5 + UP * 2.2,
            color=NM_GREEN, stroke_width=3, buff=0, tip_length=0.15,
        )
        ct_left = Text("C(t-1)", font_size=14, color=NM_GREEN)
        ct_left.next_to(cell_line, LEFT, buff=0.1)
        ct_right = Text("C(t)", font_size=14, color=NM_GREEN)
        ct_right.next_to(cell_line, RIGHT, buff=0.1)

        self.play(Write(cell_label), run_time=0.4)
        self.play(GrowArrow(cell_line), FadeIn(ct_left), FadeIn(ct_right), run_time=0.8)
        self.wait(0.4)

        # === Step 2: Show the four gates ===
        forget_gate = make_gate_box("forget", NM_PRIMARY)
        input_gate = make_gate_box("input", NM_YELLOW)
        candidate_gate = make_gate_box("candidate", NM_ORANGE)
        output_gate = make_gate_box("output", NM_BLUE)

        forget_gate.move_to(LEFT * 3.5 + UP * 0.8)
        input_gate.move_to(LEFT * 1.0 + UP * 0.8)
        candidate_gate.move_to(RIGHT * 1.5 + UP * 0.8)
        output_gate.move_to(RIGHT * 4.0 + UP * 0.8)

        gates = VGroup(forget_gate, input_gate, candidate_gate, output_gate)
        gate_labels = VGroup(
            Text("f = \u03c3(W\u2095x + W\u2095h)", font_size=11, color=NM_PRIMARY),
            Text("i = \u03c3(W\u1d62x + W\u1d62h)", font_size=11, color=NM_YELLOW),
            Text("g = tanh(W\u209cx + W\u209ch)", font_size=11, color=NM_ORANGE),
            Text("o = \u03c3(W\u2092x + W\u2092h)", font_size=11, color=NM_BLUE),
        )
        for gl, gate in zip(gate_labels, gates):
            gl.next_to(gate, DOWN, buff=0.15)

        self.play(
            LaggedStart(*[FadeIn(g, shift=UP * 0.15) for g in gates], lag_ratio=0.12),
            run_time=1.0,
        )
        self.play(
            LaggedStart(*[FadeIn(l) for l in gate_labels], lag_ratio=0.1),
            run_time=0.8,
        )
        self.wait(0.6)

        # === Step 3: Animate gate operations on the cell state ===
        # Forget gate — erases part of cell state
        forget_cross = Text("\u00d7", font_size=24, color=NM_PRIMARY)
        forget_cross.move_to(LEFT * 3.5 + UP * 2.2)
        forget_arrow = Arrow(
            forget_gate.get_top(), forget_cross.get_bottom(),
            color=NM_PRIMARY, stroke_width=1.5, buff=0.05, tip_length=0.1,
        )
        self.play(GrowArrow(forget_arrow), FadeIn(forget_cross), run_time=0.5)

        # Input gate — writes new information
        plus_sign = Text("+", font_size=24, color=NM_YELLOW)
        plus_sign.move_to(RIGHT * 0.2 + UP * 2.2)
        input_mul = Text("\u00d7", font_size=18, color=NM_YELLOW)
        input_mul.move_to(LEFT * 0.3 + UP * 1.5)
        input_arrow = Arrow(
            input_gate.get_top(), plus_sign.get_bottom() + LEFT * 0.3,
            color=NM_YELLOW, stroke_width=1.5, buff=0.05, tip_length=0.1,
        )
        cand_arrow = Arrow(
            candidate_gate.get_top(), plus_sign.get_bottom() + RIGHT * 0.3,
            color=NM_ORANGE, stroke_width=1.5, buff=0.05, tip_length=0.1,
        )
        self.play(
            GrowArrow(input_arrow), GrowArrow(cand_arrow), FadeIn(plus_sign),
            run_time=0.5,
        )

        # Output gate — reads from cell state
        out_arrow = Arrow(
            output_gate.get_top(), RIGHT * 4.0 + UP * 2.0,
            color=NM_BLUE, stroke_width=1.5, buff=0.05, tip_length=0.1,
        )
        h_label = Text("h(t) = o \u00d7 tanh(C(t))", font_size=13, color=NM_BLUE)
        h_label.next_to(output_gate, RIGHT, buff=0.3).shift(UP * 0.6)
        self.play(GrowArrow(out_arrow), FadeIn(h_label), run_time=0.5)
        self.wait(0.6)

        # === Step 4: Animate data flowing through time steps ===
        step_label = Text("Cell state persists across time", font_size=16, color=NM_GREEN, weight=BOLD)
        step_label.move_to(DOWN * 1.2)
        self.play(Write(step_label), run_time=0.5)

        # Animate a pulse traveling along the cell state line
        pulse = Dot(radius=0.12, color=NM_GREEN).set_fill(opacity=0.9)
        pulse.move_to(cell_line.get_start())
        self.play(FadeIn(pulse), run_time=0.2)
        self.play(pulse.animate.move_to(cell_line.get_end()), run_time=1.5, rate_func=linear)
        self.play(FadeOut(pulse), run_time=0.2)

        # === Step 5: Summary comparison ===
        summary = VGroup(
            Text("RNN: h(t) = tanh(Wh + Wx)  \u2192  gradient vanishes", font_size=13, color=NM_PRIMARY),
            Text("LSTM: C(t) = f\u00b7C(t-1) + i\u00b7g  \u2192  gradient highway", font_size=13, color=NM_GREEN, weight=BOLD),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        summary.move_to(DOWN * 2.2)
        self.play(
            LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in summary], lag_ratio=0.2),
            run_time=0.8,
        )
        self.wait(1.6)

        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
