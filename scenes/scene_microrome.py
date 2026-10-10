"""
Scene: ROME Knowledge Editing
Script: microrome.py
Description: One closed-form rank-one update of an MLP matrix rewrites one stored fact
"""

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

# Lighter companions to the palette: keys need a blue that reads on the dark background,
# and secondary captions a muted gray.
KEY_COLOR = "#4fa3e0"
MUTED = "#8a8aa8"


# Every number shown below is copied from the default run of no-magic's
# 02-alignment/microrome.py (seed 42, CPython 3.12.8): the "thom" edit lines and the
# AGGREGATE table. Vectors and matrices are drawn schematically (cell colors encode no
# values); metric bar heights are proportional to the printed values.
EDIT_SUBJECT = "thom"
OLD_CITY = "Halen"
NEW_CITY = "Cavo"
NEIGHBORS = ("tavi", "yulm")  # the other two subjects whose city is Halen
CATEGORY = "tower"
VALUE_STEPS = 21
VALUE_LOSS_START = "16.520"
VALUE_LOSS_END = "0.038"
CONSTRAINT_RESIDUAL = "4.4e-16"
THOM_P_NEW = "1.0000"
THOM_P_OLD = "0.0000"
THOM_IDENTITY_NS = "0.1625"
# AGGREGATE means over the six edits: (ES, PS, NS, BLEED, ESS)
ROME_MEANS = (0.9667, 0.8694, 1.0000, 0.0000, 1.0000)
IDENTITY_MEANS = (0.8333, 0.7917, 0.6865, 0.0281, 1.0000)


def cell_strip(count: int, color: str, cell: float, vertical: bool = False) -> VGroup:
    """A vector drawn as a strip of equal cells (schematic: no values encoded)."""
    cells = VGroup(
        *[
            Square(side_length=cell, stroke_width=0.6, stroke_color=NM_GRID).set_fill(
                color, opacity=0.75
            )
            for _ in range(count)
        ]
    )
    cells.arrange(DOWN if vertical else RIGHT, buff=0)
    return cells


def cell_grid(rows: int, cols: int, color: str, cell: float, opacity: float = 0.35) -> VGroup:
    """A matrix drawn as rows x cols cells (schematic: no values encoded)."""
    grid = VGroup(
        *[
            Rectangle(width=cell, height=cell, stroke_width=0.3, stroke_color=NM_GRID).set_fill(
                color, opacity=opacity
            )
            for _ in range(rows * cols)
        ]
    )
    grid.arrange_in_grid(rows=rows, cols=cols, buff=0)
    return grid


def token_row(tokens: list[str], highlight: int, font_size: int = 20) -> VGroup:
    """Prompt tokens in boxes; the subject token at index `highlight` is colored."""
    boxes = VGroup()
    for i, tok in enumerate(tokens):
        color = NM_ORANGE if i == highlight else NM_TEXT
        label = Text(tok, font_size=font_size, color=color)
        box = SurroundingRectangle(label, buff=0.1, color=color, stroke_width=1.5)
        boxes.add(VGroup(box, label))
    boxes.arrange(RIGHT, buff=0.15)
    return boxes


def metric_bars(values: tuple[float, ...], color: str, max_height: float = 1.6) -> VGroup:
    """One bar per metric with the printed program value above it."""
    bars = VGroup()
    for value in values:
        bar = Rectangle(width=0.42, height=max(value * max_height, 0.03), color=color)
        bar.set_fill(color, opacity=0.75)
        label = Text(f"{value:.4f}", font_size=13, color=NM_TEXT)
        label.next_to(bar, UP, buff=0.06)
        bars.add(VGroup(bar, label))
    bars.arrange(RIGHT, buff=0.32, aligned_edge=DOWN)
    return bars


class RomeScene(NoMagicScene):
    title_text = "ROME Knowledge Editing"
    subtitle_text = "Rewrite one stored fact with a rank-one update of an MLP matrix"

    def animate(self) -> None:
        self.show_memory()
        self.show_key()
        self.show_value()
        self.show_update()
        self.show_checks()
        self.show_identity_control()

    def show_memory(self) -> None:
        """The trained MLP output matrix maps a key at the subject token to a value."""
        header = Text("A fact lives in an MLP matrix", font_size=28, color=NM_TEXT, weight=BOLD)
        header.to_edge(UP, buff=0.45)
        prompt = token_row(["the", EDIT_SUBJECT, "sits-in"], highlight=1)
        prompt.move_to(LEFT * 4.3 + UP * 1.4)
        answer = Text(f"→ {OLD_CITY}", font_size=22, color=NM_GREEN)
        answer.next_to(prompt, RIGHT, buff=0.25)
        trained = Text("decoder trained from random weights", font_size=16, color=NM_TEXT)
        trained.next_to(prompt, DOWN, buff=0.25).align_to(prompt, LEFT)
        self.play(FadeIn(header), FadeIn(prompt), run_time=0.9)
        self.play(FadeIn(answer), FadeIn(trained), run_time=0.7)

        key = cell_strip(64, KEY_COLOR, 0.04, vertical=True)
        key.move_to(LEFT * 3.2 + DOWN * 1.3)
        key_label = Text("key k\n(64)", font_size=16, color=KEY_COLOR)
        key_label.next_to(key, LEFT, buff=0.2)
        w_proj = cell_grid(16, 64, NM_PURPLE, 0.07)
        w_proj.move_to(RIGHT * 0.6 + DOWN * 1.3)
        w_label = Text("W_proj  16 × 64", font_size=18, color=NM_PURPLE)
        w_label.next_to(w_proj, UP, buff=0.2)
        value = cell_strip(16, NM_GREEN, 0.075, vertical=True)
        value.move_to(RIGHT * 4.4 + DOWN * 1.3)
        value_label = Text("value v\n(16)", font_size=16, color=NM_GREEN)
        value_label.next_to(value, RIGHT, buff=0.2)
        arrow_in = Arrow(key.get_right(), w_proj.get_left(), buff=0.15, color=NM_TEXT)
        arrow_out = Arrow(w_proj.get_right(), value.get_left(), buff=0.15, color=NM_TEXT)
        self.play(FadeIn(key), FadeIn(key_label), run_time=0.7)
        self.play(GrowArrow(arrow_in), FadeIn(w_proj), FadeIn(w_label), run_time=1.0)
        self.play(GrowArrow(arrow_out), FadeIn(value), FadeIn(value_label), run_time=0.8)
        note = Text(
            "ROME's view: W K ≈ V, a linear key → value memory (Sec. 3.1)",
            font_size=18,
            color=NM_YELLOW,
        )
        note.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(1.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)

    def show_key(self) -> None:
        """k*: the subject token's MLP key, averaged over prompts with different prefixes."""
        header = Text(
            "Key k*: average the subject's key over prefixes",
            font_size=26,
            color=NM_TEXT,
            weight=BOLD,
        )
        header.to_edge(UP, buff=0.45)
        self.play(FadeIn(header), run_time=0.6)
        prefixes = [[], ["a"], ["old", "the"], ["one", "new", "big"]]
        rows = VGroup()
        for prefix in prefixes:
            tokens = [*prefix, EDIT_SUBJECT, "sits-in"]
            row = token_row(tokens, highlight=len(prefix), font_size=16)
            strip = cell_strip(16, KEY_COLOR, 0.1)
            group = VGroup(row, strip).arrange(RIGHT, buff=0.5)
            rows.add(group)
        rows.arrange(DOWN, buff=0.28, aligned_edge=RIGHT)
        rows.move_to(LEFT * 1.6 + DOWN * 0.2)
        for prompt_row in rows:
            self.play(FadeIn(prompt_row[0]), FadeIn(prompt_row[1]), run_time=0.45)
        k_star = cell_strip(16, NM_YELLOW, 0.1)
        k_star.next_to(rows, RIGHT, buff=1.2)
        k_label = Text("k*  (64-dim, drawn short)", font_size=18, color=NM_YELLOW)
        k_label.next_to(k_star, RIGHT, buff=0.25)
        merges = [
            Arrow(
                prompt_row[1].get_right(),
                k_star.get_left(),
                buff=0.1,
                stroke_width=2,
                color=MUTED,
                max_tip_length_to_length_ratio=0.08,
            )
            for prompt_row in rows
        ]
        self.play(LaggedStart(*[GrowArrow(a) for a in merges], lag_ratio=0.15), run_time=0.9)
        self.play(FadeIn(k_star), FadeIn(k_label), run_time=0.7)
        caption = VGroup(
            Text(
                "k* = (1/N) Σ_j k(x_j + s),  N = 20 prefixes of 0-3 fillers (Eq. 3)",
                font_size=17,
                color=NM_TEXT,
            ),
            Text(
                "no attention before the MLP: the key depends on subject and position only",
                font_size=15,
                color=NM_YELLOW,
            ),
        ).arrange(DOWN, buff=0.15)
        caption.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(caption), run_time=0.7)
        self.wait(1.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)

    def show_value(self) -> None:
        """v*: gradient descent on a free vector z injected as the MLP output; weights frozen."""
        header = Text(
            "Value v*: gradient on the injected MLP output",
            font_size=26,
            color=NM_TEXT,
            weight=BOLD,
        )
        header.to_edge(UP, buff=0.45)
        prompt = token_row(["the", EDIT_SUBJECT, "sits-in"], highlight=1)
        prompt.move_to(LEFT * 3.6 + UP * 1.3)
        z = cell_strip(16, NM_PRIMARY, 0.11, vertical=True)
        z.next_to(prompt[1], DOWN, buff=0.35)
        z_label = Text("m := z", font_size=18, color=NM_PRIMARY)
        z_label.next_to(z, LEFT, buff=0.2)
        target = Text(f"target o* = {NEW_CITY}", font_size=20, color=NM_GREEN)
        target.next_to(prompt, RIGHT, buff=0.4)
        lock = Text("all weights frozen", font_size=16, color=NM_YELLOW)
        lock.next_to(z, DOWN, buff=0.3)
        self.play(FadeIn(header), FadeIn(prompt), run_time=0.7)
        self.play(FadeIn(z), FadeIn(z_label), FadeIn(target), FadeIn(lock), run_time=0.9)

        objective = VGroup(
            Text("L(z) = mean_j −log P[o* | x_j + p; m := z]", font_size=19, color=NM_TEXT),
            Text(
                "      + λ · KL(P[· | subject is-a; m := z] ‖ P[· | subject is-a])",
                font_size=17,
                color=NM_TEXT,
            ),
            Text(
                "λ = 100 (paper App. E.5): the category must not drift (Eq. 4)",
                font_size=15,
                color=NM_YELLOW,
            ),
        ).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        objective.move_to(RIGHT * 1.6 + DOWN * 0.2)
        self.play(Write(objective[0]), run_time=1.1)
        self.play(FadeIn(objective[1]), FadeIn(objective[2]), run_time=0.8)
        grad = CurvedArrow(
            objective.get_left() + DOWN * 0.1,
            z.get_right() + RIGHT * 0.05,
            angle=-TAU / 8,
            color=NM_PRIMARY,
            stroke_width=2.5,
        )
        self.play(Create(grad), run_time=0.7)
        result = Text(
            f"{EDIT_SUBJECT}: Adam on z only, L {VALUE_LOSS_START} → {VALUE_LOSS_END} "
            f"in {VALUE_STEPS} steps  ⇒  v*",
            font_size=18,
            color=NM_GREEN,
        )
        result.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(result, shift=UP * 0.2), run_time=0.7)
        self.wait(1.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)

    def show_update(self) -> None:
        """The rank-one outer product Λ (C⁻¹k*)ᵀ is added to a copy of W_proj."""
        header = Text(
            "Insert (k*, v*) with one rank-one update",
            font_size=26,
            color=NM_TEXT,
            weight=BOLD,
        )
        header.to_edge(UP, buff=0.45)
        formula = VGroup(
            Text("Ŵ = W + Λ (C⁻¹k*)ᵀ", font_size=24, color=NM_TEXT),
            Text(
                "Λ = (v* − W k*) / ((C⁻¹k*)ᵀ k*)     C = K Kᵀ from keys at every position",
                font_size=16,
                color=NM_TEXT,
            ),
        ).arrange(DOWN, buff=0.15)
        formula.next_to(header, DOWN, buff=0.3)
        self.play(FadeIn(header), Write(formula[0]), run_time=1.1)
        self.play(FadeIn(formula[1]), run_time=0.6)

        lam = cell_strip(16, NM_GREEN, 0.09, vertical=True)
        u = cell_strip(64, KEY_COLOR, 0.085)
        delta = cell_grid(16, 64, NM_PRIMARY, 0.085, opacity=0.6)
        delta.move_to(DOWN * 1.15 + RIGHT * 0.7)
        lam.next_to(delta, LEFT, buff=0.25)
        u.next_to(delta, UP, buff=0.2)
        lam_label = Text("Λ (16)", font_size=16, color=NM_GREEN)
        lam_label.next_to(lam, LEFT, buff=0.15)
        u_label = Text("u = C⁻¹k*  (64)", font_size=16, color=KEY_COLOR)
        u_label.next_to(u, LEFT, buff=0.15)
        self.play(FadeIn(lam), FadeIn(lam_label), FadeIn(u), FadeIn(u_label), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(row) for row in self.grid_rows(delta, 16)], lag_ratio=0.08),
            run_time=1.2,
        )
        delta_label = Text(
            "ΔW = Λ uᵀ added to a fresh copy of W_proj: every entry moves, one direction",
            font_size=16,
            color=NM_PRIMARY,
        )
        delta_label.next_to(delta, DOWN, buff=0.2)
        self.play(FadeIn(delta_label), run_time=0.5)
        checks = Text(
            f"printed checks: rank=1   |Ŵk* − v*| = {CONSTRAINT_RESIDUAL}   only W_proj changed",
            font_size=16,
            color=NM_YELLOW,
        )
        checks.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(checks), run_time=0.6)
        self.wait(1.8)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)

    def grid_rows(self, grid: VGroup, rows: int) -> list[VGroup]:
        """Split an arranged grid back into its rows for a row-by-row reveal."""
        cols = len(grid) // rows
        return [VGroup(*grid[r * cols : (r + 1) * cols]) for r in range(rows)]

    def show_checks(self) -> None:
        """Before and after: the edited fact, its neighbors and its essence."""
        header = Text("Before and after the edit", font_size=26, color=NM_TEXT, weight=BOLD)
        header.to_edge(UP, buff=0.45)
        self.play(FadeIn(header), run_time=0.5)
        rows = [
            (f"{EDIT_SUBJECT} sits-in", OLD_CITY, NEW_CITY, NM_PRIMARY, "edited fact"),
            (f"{NEIGHBORS[0]} sits-in", OLD_CITY, OLD_CITY, NM_GREEN, "neighbor (same city)"),
            (f"{NEIGHBORS[1]} sits-in", OLD_CITY, OLD_CITY, NM_GREEN, "neighbor (same city)"),
            (f"{EDIT_SUBJECT} is-a", CATEGORY, CATEGORY, NM_GREEN, "essence (category)"),
        ]
        table = VGroup()
        for prompt, before, after, color, kind in rows:
            line = VGroup(
                Text(prompt, font_size=19, color=NM_TEXT),
                Text(before, font_size=19, color=NM_TEXT),
                Text("→", font_size=19, color=NM_TEXT),
                Text(after, font_size=19, color=color),
                Text(kind, font_size=15, color=MUTED),
            ).arrange(RIGHT, buff=0.4)
            table.add(line)
        table.arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        table.move_to(UP * 0.2)
        for table_line in table:
            self.play(FadeIn(table_line, shift=RIGHT * 0.2), run_time=0.5)
        summary = VGroup(
            Text(
                f"{EDIT_SUBJECT}: P[{NEW_CITY}] = {THOM_P_NEW}, P[{OLD_CITY}] = {THOM_P_OLD} "
                "(mean over 20 prefixes)",
                font_size=16,
                color=NM_TEXT,
            ),
            Text(
                "six edits: efficacy 0.9667 · paraphrase 0.8694 · neighborhood 1.0000 · "
                "essence 1.0000",
                font_size=16,
                color=NM_YELLOW,
            ),
        ).arrange(DOWN, buff=0.15)
        summary.to_edge(DOWN, buff=0.4)
        self.play(FadeIn(summary), run_time=0.7)
        self.wait(1.8)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)

    def show_identity_control(self) -> None:
        """Same v*, but u = k* (C = I): the update leaks into neighboring keys."""
        header = Text("Why C⁻¹? The C = I control", font_size=26, color=NM_TEXT, weight=BOLD)
        header.to_edge(UP, buff=0.45)
        sub = Text(
            "same v*, address u = k* instead of C⁻¹k* (report-only control)",
            font_size=17,
            color=NM_TEXT,
        )
        sub.next_to(header, DOWN, buff=0.2)
        self.play(FadeIn(header), FadeIn(sub), run_time=0.7)
        names = VGroup(
            *[Text(n, font_size=15, color=NM_TEXT) for n in ("ES", "PS", "NS", "BLEED", "ESS")]
        )
        rome_bars = metric_bars(ROME_MEANS, NM_GREEN)
        identity_bars = metric_bars(IDENTITY_MEANS, NM_ORANGE)
        rome_bars.move_to(LEFT * 3.3 + DOWN * 0.5)
        identity_bars.move_to(RIGHT * 3.3 + DOWN * 0.5)
        rome_names = names.copy()
        identity_names = names.copy()
        for labels, bars in ((rome_names, rome_bars), (identity_names, identity_bars)):
            for label, bar in zip(labels, bars):
                label.next_to(bar, DOWN, buff=0.12)
        rome_title = Text("ROME (C⁻¹k*)", font_size=18, color=NM_GREEN)
        rome_title.next_to(rome_bars, UP, buff=0.35)
        identity_title = Text("C = I (k*)", font_size=18, color=NM_ORANGE)
        identity_title.next_to(identity_bars, UP, buff=0.35)
        self.play(FadeIn(rome_bars), FadeIn(rome_names), FadeIn(rome_title), run_time=0.9)
        self.play(
            FadeIn(identity_bars), FadeIn(identity_names), FadeIn(identity_title), run_time=0.9
        )
        focus = SurroundingRectangle(identity_bars[2], color=NM_PRIMARY, buff=0.08)
        self.play(Create(focus), run_time=0.5)
        note = VGroup(
            Text(
                f"neighborhood mean 1.0000 → 0.6865  ({EDIT_SUBJECT} with C = I: "
                f"{THOM_IDENTITY_NS})",
                font_size=16,
                color=NM_PRIMARY,
            ),
            Text(
                "means over six edits · toy model, invented facts, seed 42 · not GPT-2 XL",
                font_size=14,
                color=NM_TEXT,
            ),
        ).arrange(DOWN, buff=0.12)
        note.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(2.2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
