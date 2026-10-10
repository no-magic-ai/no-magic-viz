"""
Scene: Knowledge Distillation
Script: microdistill.py
Description: A frozen teacher's temperature-softened probabilities train a smaller student
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import (
    NM_GREEN,
    NM_GRID,
    NM_ORANGE,
    NM_PRIMARY,
    NM_PURPLE,
    NM_TEXT,
    NM_YELLOW,
    NoMagicScene,
)
from manim import *

CLASS_COLORS = [NM_PRIMARY, NM_GREEN, NM_ORANGE]
# Logits used only to illustrate the softmax arithmetic below; they are not program output.
EXAMPLE_LOGITS = [4.0, 1.0, 0.0]


def softmax(logits: list[float], temperature: float) -> list[float]:
    """softmax(z / T), stabilized by subtracting the max scaled logit."""
    scaled = [z / temperature for z in logits]
    shift = max(scaled)
    exps = [math.exp(s - shift) for s in scaled]
    total = sum(exps)
    return [e / total for e in exps]


def make_mlp(widths: list[int], color: str, height: float = 2.4) -> VGroup:
    """Columns of neuron dots joined by thin edges: one dot per unit of each declared width."""
    columns = VGroup()
    for width in widths:
        column = VGroup(*[Dot(radius=0.06, color=color) for _ in range(width)])
        column.arrange(DOWN, buff=height / width - 0.12)
        columns.add(column)
    columns.arrange(RIGHT, buff=0.8)
    edges = VGroup()
    for left, right in zip(columns[:-1], columns[1:]):
        for a in left:
            for b in right:
                edges.add(Line(a.get_center(), b.get_center(), stroke_width=0.6, color=NM_GRID))
    return VGroup(edges, columns)


def make_bars(probs: list[float], label: str, max_height: float = 1.8) -> VGroup:
    """Three probability bars with their values printed above them."""
    bars = VGroup()
    for p, color in zip(probs, CLASS_COLORS):
        bar = Rectangle(width=0.45, height=max(p * max_height, 0.02), color=color, fill_opacity=0.7)
        value = Text(f"{p:.2f}", font_size=16, color=NM_TEXT)
        value.next_to(bar, UP, buff=0.08)
        bars.add(VGroup(bar, value))
    bars.arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
    caption = Text(label, font_size=18, color=NM_TEXT)
    caption.next_to(bars, DOWN, buff=0.25)
    return VGroup(bars, caption)


class DistillScene(NoMagicScene):
    title_text = "Knowledge Distillation"
    subtitle_text = "A small student learns from a frozen teacher's soft targets"

    def animate(self) -> None:
        self.show_teacher()
        self.show_temperature()
        self.show_student()

    def show_teacher(self) -> None:
        """Toy clusters, then a teacher trained on hard labels and frozen."""
        header = Text(
            "Train a teacher on labelled toy clusters", font_size=26, color=NM_TEXT, weight=BOLD
        )
        header.to_edge(UP, buff=0.5)
        plane = NumberPlane(
            x_range=[-2, 2, 1],
            y_range=[-1, 2, 1],
            x_length=4.0,
            y_length=3.0,
            background_line_style={"stroke_color": NM_GRID, "stroke_width": 1},
        )
        plane.move_to(LEFT * 3.6 + DOWN * 0.4)
        # Schematic points placed on a fixed ring around each center (illustration only).
        centers = [(-1.0, 0.0), (1.0, 0.0), (0.0, 1.25)]
        dots = VGroup()
        for (cx, cy), color in zip(centers, CLASS_COLORS):
            for k in range(10):
                angle = TAU * k / 10
                r = 0.18 + 0.12 * (k % 3)
                dots.add(
                    Dot(
                        plane.c2p(cx + r * math.cos(angle), cy + r * math.sin(angle)),
                        radius=0.05,
                        color=color,
                    )
                )
        data_note = Text(
            "3 toy Gaussian clusters · schematic, not program data", font_size=16, color=NM_TEXT
        )
        data_note.next_to(plane, DOWN, buff=0.25)
        self.play(FadeIn(header), Create(plane), run_time=1.0)
        self.play(
            LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.02), FadeIn(data_note), run_time=1.2
        )

        teacher = make_mlp([2, 16, 3], NM_PURPLE)
        teacher.move_to(RIGHT * 3.0 + DOWN * 0.2)
        teacher_label = Text("teacher 2 → 16 → 3 · 99 parameters", font_size=18, color=NM_PURPLE)
        teacher_label.next_to(teacher, UP, buff=0.3)
        train_note = Text(
            "trained on hard labels: mean cross-entropy, SGD", font_size=16, color=NM_TEXT
        )
        train_note.next_to(teacher, DOWN, buff=0.3)
        self.play(Create(teacher), FadeIn(teacher_label), run_time=1.4)
        self.play(FadeIn(train_note), run_time=0.6)

        lock = Text("frozen: weight digest checked after transfer", font_size=18, color=NM_YELLOW)
        lock.next_to(train_note, DOWN, buff=0.3)
        frame = SurroundingRectangle(teacher, color=NM_YELLOW, buff=0.15)
        self.play(Create(frame), FadeIn(lock), run_time=0.8)
        self.wait(1.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)

    def show_temperature(self) -> None:
        """The same logits at T = 1 and T = 2: softer targets expose the wrong-class ranking."""
        header = Text("Soft targets: softmax(z / T)", font_size=26, color=NM_TEXT, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        logits = Text(
            "example logits z = [4, 1, 0]  (illustration, not program output)",
            font_size=18,
            color=NM_TEXT,
        )
        logits.next_to(header, DOWN, buff=0.3)
        hard = make_bars([1.0, 0.0, 0.0], "one-hot label")
        t1 = make_bars(softmax(EXAMPLE_LOGITS, 1.0), "T = 1")
        t2 = make_bars(softmax(EXAMPLE_LOGITS, 2.0), "T = 2")
        group = VGroup(hard, t1, t2).arrange(RIGHT, buff=1.2, aligned_edge=DOWN)
        group.move_to(DOWN * 0.5)
        self.play(FadeIn(header), FadeIn(logits), run_time=0.8)
        self.play(FadeIn(hard), run_time=0.6)
        self.play(FadeIn(t1), run_time=0.7)
        self.play(TransformFromCopy(t1, t2), run_time=1.0)
        note = Text(
            "higher T keeps the order but lifts the wrong classes — information a label drops",
            font_size=18,
            color=NM_YELLOW,
        )
        note.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(2.0)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)

    def show_student(self) -> None:
        """A smaller student, the mixed objective, its gradient and T = 1 inference."""
        teacher = make_mlp([2, 16, 3], NM_PURPLE, height=2.0)
        teacher.move_to(LEFT * 4.2 + UP * 1.2)
        t_label = Text("frozen teacher → p_T", font_size=16, color=NM_PURPLE)
        t_label.next_to(teacher, UP, buff=0.2)
        student = make_mlp([2, 4, 3], NM_GREEN, height=1.4)
        student.move_to(LEFT * 4.2 + DOWN * 1.6)
        s_label = Text("student 2 → 4 → 3 · 27 parameters → q_T, q₁", font_size=16, color=NM_GREEN)
        s_label.next_to(student, DOWN, buff=0.2)
        self.play(FadeIn(teacher), FadeIn(t_label), FadeIn(student), FadeIn(s_label), run_time=1.0)

        objective = VGroup(
            Text("loss = 0.9 · T² · KL(p_T ‖ q_T) + 0.1 · CE(y, q₁)", font_size=22, color=NM_TEXT),
            Text("T = 2 · mean over the training batch (1/B)", font_size=16, color=NM_TEXT),
            Text(
                "∂loss/∂z = 0.9 · T · (q_T − p_T) + 0.1 · (q₁ − onehot(y))",
                font_size=20,
                color=NM_PRIMARY,
            ),
            Text(
                "T² offsets the 1/T² shrinkage of soft-target gradients",
                font_size=16,
                color=NM_YELLOW,
            ),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        objective.move_to(RIGHT * 2.2 + UP * 0.9)
        self.play(Write(objective[0]), run_time=1.4)
        self.play(FadeIn(objective[1]), run_time=0.5)
        self.play(FadeIn(objective[2]), run_time=0.9)
        self.play(FadeIn(objective[3]), run_time=0.6)

        grad = CurvedArrow(
            objective.get_left() + DOWN * 0.6,
            student.get_right() + RIGHT * 0.1,
            angle=-TAU / 8,
            color=NM_PRIMARY,
            stroke_width=2.5,
        )
        grad_note = Text("SGD updates the student only", font_size=16, color=NM_PRIMARY)
        grad_note.next_to(grad, DOWN, buff=0.1)
        self.play(Create(grad), FadeIn(grad_note), run_time=0.9)

        infer = VGroup(
            Text("inference: both models use softmax(z / 1)", font_size=18, color=NM_TEXT),
            Text("held-out points are reported, never used to tune", font_size=16, color=NM_TEXT),
        ).arrange(DOWN, buff=0.2)
        infer.move_to(RIGHT * 2.2 + DOWN * 2.6)
        self.play(FadeIn(infer, shift=UP * 0.2), run_time=0.8)
        self.wait(2.2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
