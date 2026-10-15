"""
Scene: Eval Error Bars
Script: microerrorbars.py
Description: Small-n coverage of 95% intervals, paired against unpaired
widths, then the question count needed to see an effect
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import (
    NM_GREEN,
    NM_GRID,
    NM_ORANGE,
    NM_PRIMARY,
    NM_TEXT,
    NM_YELLOW,
    NoMagicScene,
)
from manim import *
from manim.typing import Point3D

# A muted gray for captions and the unpaired extension rows.
MUTED = "#8a8aa8"

# Provenance. Every printed number below is copied from the pinned seed-42 default output of
# no-magic 01-foundations/microerrorbars.py (issue #55; output SHA-256 c6a260d8 without timing;
# CPython 3.12.8). The scene does not run or read that script. Plain arithmetic on
# displayed values is the only derivation. The model arms are toy synthetic classifiers, the
# Part A scores are binary with K = 1 answer per question, there is one seed and no clustering.
# Reference: Miller, "Adding Error Bars to Evals", arXiv 2411.00640. Miller does not claim that
# CLT intervals under-cover at small n; the coverage study and the Wilson reference are this
# program's extension, citing Brown, Cai & DasGupta (2001), Statistical Science 16(2),
# doi:10.1214/ss/1009213286.
Z_CRITICAL = 1.959964  # stdout line 1; the one multiplier used by every interval
Z_BETA = "0.841621"  # stdout line 1
CONFIDENCE_LABEL = "95%"  # stdout line 2
REPLICATES_LABEL = "1000"  # stdout line 2: R = 1000 evals per cell
TARGET_COVERAGE = "0.950"  # stdout line 3
ALPHA_LABEL, BETA_LABEL = "0.05", "0.2"  # stdout line 46

# Part A, mu = 0.95, n = 30 (stdout lines 22-24): coverage of the true accuracy and the share of
# simulated evals whose interval has zero width.
TRUE_ACCURACY = 0.95
TRUE_ACCURACY_LABEL = "0.95"
N_SMALL = 30
COVERAGE_CLT, COVERAGE_BOOTSTRAP, COVERAGE_WILSON = "0.797", "0.789", "0.934"
ZERO_WIDTH_SHARE = "0.201"  # CLT and bootstrap alike (lines 22-23)
ZERO_WIDTH_WILSON = "0.000"  # line 24

# ILLUSTRATIVE, not measured: the number of correct answers (out of N_SMALL) behind each drawn
# interval. These counts are hand-picked so that the picture looks like a typical batch of
# small evals; every interval is then computed from its count with the CLT formula
# (accuracy +/- Z_CRITICAL * sqrt(p (1 - p) / (n - 1))). Nothing about them is a measurement; the
# measured coverage numbers are the ones printed above.
ILLUSTRATIVE_CORRECT = (
    29,
    28,
    30,
    27,
    29,
    26,
    30,
    28,
    29,
    25,
    27,
    29,
    30,
    28,
    26,
    29,
    27,
    28,
    30,
    29,
)

# Number-line scale for the illustrative intervals: axis labels only, not data.
AXIS_MIN, AXIS_MAX = 0.65, 1.05
AXIS_TICKS = (0.70, 0.80, 0.90, 1.00)
AXIS_LEFT_X, AXIS_LENGTH = -6.8, 6.4
AXIS_Y = -1.85
ROW_TOP_Y, ROW_STEP = 2.0, 0.18

# Part B, n = 100 (stdout lines 36-37, 42): interval widths for the pool difference A - B.
N_PAIRED = 100
WIDTH_UNPAIRED, WIDTH_PAIRED = 0.1863, 0.1374
COVERAGE_UNPAIRED, COVERAGE_PAIRED = "0.990", "0.943"
WIDTH_RATIO = "0.738"
POOL_DIFFERENCE = "0.0511"
CORRELATION = "0.4530"

# Part C (stdout lines 46-56, 63): minimum detectable effect at alpha = 0.05, beta = 0.2.
# Rows are (n, paired, unpaired). The unpaired rows replace omega^2 with Var(s_A) + Var(s_B), an
# extension of Miller's Eq. 10 (his Eq. 9 assumes paired analysis).
MDE_ROWS = (
    (30, 0.1816, 0.2441),
    (100, 0.0995, 0.1337),
    (500, 0.0445, 0.0598),
    (1000, 0.0315, 0.0423),
)
OMEGA_SQUARED_PAIRED = "0.1260"  # line 47
VARIANCE_UNPAIRED = "0.2278"  # line 47
# Miller Sec. 5 worked example, Eq. 9 (stdout line 63: n = 968.997, unrounded). Miller calls
# the parameters fictional.
MILLER_OMEGA_SQUARED, MILLER_DELTA, MILLER_N = "1/9", "0.03", "969"

# Limits (stdout lines 22-27, 41): findings the scene states rather than hides.
PAIRED_COVERAGE_N30 = "0.919"
CLT_COVERAGE_N100, BOOTSTRAP_COVERAGE_N100 = "0.863", "0.938"


def axis_x(value: float) -> float:
    """Scene x of an accuracy value on the illustrative number line."""
    return AXIS_LEFT_X + (value - AXIS_MIN) / (AXIS_MAX - AXIS_MIN) * AXIS_LENGTH


def at(x: float, y: float) -> Point3D:
    """A scene point."""
    return np.array([x, y, 0.0])


def clt_interval(correct: int, n: int) -> tuple[float, float, float]:
    """(accuracy, low, high) of the CLT interval for a binary eval with `correct` of n right."""
    p_hat = correct / n
    half_width = Z_CRITICAL * math.sqrt(p_hat * (1.0 - p_hat) / (n - 1))
    return p_hat, p_hat - half_width, p_hat + half_width


def make_bar(
    value: float,
    max_value: float,
    max_height: float,
    width: float,
    color: str,
    label_size: int,
) -> VGroup:
    """One bar; height proportional to the printed value (4 decimals), label above."""
    rect = Rectangle(width=width, height=value / max_value * max_height, color=color)
    rect.set_fill(color, opacity=0.8)
    text = Text(f"{value:.4f}", font_size=label_size, color=NM_TEXT)
    text.next_to(rect, UP, buff=0.08)
    return VGroup(rect, text)


def stat_table(
    rows: tuple[tuple[str, str], ...],
    colors: tuple[str, ...],
    name_x: float,
    value_x: float,
    top_y: float,
    step: float,
    name_size: int,
    value_size: int,
) -> VGroup:
    """Rows of name (left-aligned at name_x) and bold value (left-aligned at value_x)."""
    table = VGroup()
    for i, ((name, value), color) in enumerate(zip(rows, colors)):
        y = top_y - i * step
        name_text = Text(name, font_size=name_size, color=NM_TEXT)
        name_text.move_to(at(name_x, y), aligned_edge=LEFT)
        value_text = Text(value, font_size=value_size, color=color, weight=BOLD)
        value_text.move_to(at(value_x, y), aligned_edge=LEFT)
        table.add(VGroup(name_text, value_text))
    return table


def bullet_list(lines: tuple[str, ...], font_size: int) -> VGroup:
    """Left-aligned items, each with a dot."""
    items = VGroup()
    for line in lines:
        dot = Dot(radius=0.06, color=NM_PRIMARY)
        text = Text(line, font_size=font_size, color=NM_TEXT, line_spacing=0.9)
        items.add(VGroup(dot, text).arrange(RIGHT, buff=0.25, aligned_edge=UP))
        dot.shift(DOWN * 0.12)
    items.arrange(DOWN, buff=0.35, aligned_edge=LEFT)
    return items


class ErrorBarsScene(NoMagicScene):
    title_text = "Eval Error Bars"
    subtitle_text = "Coverage, pairing and the questions an eval needs"

    def animate(self) -> None:
        self.show_coverage()
        self.show_paired()
        self.show_questions()
        self.show_limits()

    def clear_all(self, run_time: float = 0.6) -> None:
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)

    def show_coverage(self) -> None:
        """Illustrative CLT intervals at small n, then the program's measured coverage."""
        header = Text(
            f"{CONFIDENCE_LABEL} CLT intervals, {N_SMALL} questions per eval, true accuracy "
            f"{TRUE_ACCURACY_LABEL}",
            font_size=28,
            color=NM_TEXT,
        )
        header.to_edge(UP, buff=0.4)
        self.play(FadeIn(header), run_time=0.6)

        # Number line, the shaded impossible zone above 1.00 and the true accuracy.
        zone_top = ROW_TOP_Y + 0.25
        zone_width = axis_x(AXIS_MAX) - axis_x(1.0)
        zone = Rectangle(
            width=zone_width,
            height=zone_top - AXIS_Y,
            stroke_width=0,
            fill_color=NM_GRID,
            fill_opacity=0.6,
        )
        zone.move_to(at(axis_x(1.0) + zone_width / 2, (zone_top + AXIS_Y) / 2))
        axis = Line(at(axis_x(AXIS_MIN), AXIS_Y), at(axis_x(AXIS_MAX), AXIS_Y), color=MUTED)
        tick_marks = VGroup()
        for tick in AXIS_TICKS:
            mark = Line(
                at(axis_x(tick), AXIS_Y - 0.08),
                at(axis_x(tick), AXIS_Y + 0.08),
                color=MUTED,
            )
            tick_label = Text(f"{tick:.2f}", font_size=20, color=MUTED)
            tick_label.next_to(mark, DOWN, buff=0.1)
            tick_marks.add(mark, tick_label)
        axis_note = Text(
            "each row: one simulated eval's CLT interval\n"
            "grey zone above 1.00 cannot be an accuracy",
            font_size=18,
            color=MUTED,
            line_spacing=0.9,
        )
        axis_note.move_to(at(AXIS_LEFT_X + AXIS_LENGTH / 2, AXIS_Y - 0.9))
        true_line = DashedLine(
            at(axis_x(TRUE_ACCURACY), zone_top),
            at(axis_x(TRUE_ACCURACY), AXIS_Y),
            color=NM_YELLOW,
        )
        true_label = Text(
            f"true accuracy {TRUE_ACCURACY_LABEL}",
            font_size=22,
            color=NM_YELLOW,
            weight=BOLD,
        )
        true_label.move_to(at(axis_x(TRUE_ACCURACY), zone_top + 0.28))
        self.play(
            FadeIn(zone),
            Create(axis),
            FadeIn(tick_marks),
            FadeIn(axis_note),
            Create(true_line),
            FadeIn(true_label),
            run_time=1.2,
        )

        # Illustrative intervals: counts are made up (see ILLUSTRATIVE_CORRECT).
        rows = VGroup()
        for i, correct in enumerate(ILLUSTRATIVE_CORRECT):
            p_hat, low, high = clt_interval(correct, N_SMALL)
            y = ROW_TOP_Y - i * ROW_STEP
            covers = low <= TRUE_ACCURACY <= high
            color = NM_GREEN if covers else NM_PRIMARY
            if high > low:
                row = VGroup(
                    Line(at(axis_x(low), y), at(axis_x(high), y), color=color, stroke_width=4),
                    Dot(at(axis_x(p_hat), y), radius=0.05, color=NM_TEXT),
                )
            else:
                row = VGroup(Dot(at(axis_x(p_hat), y), radius=0.07, color=color))
            rows.add(row)
        illustrative = Text(
            f"ILLUSTRATIVE intervals: made-up counts\ncorrect out of {N_SMALL}, not measured data",
            font_size=20,
            color=NM_YELLOW,
            line_spacing=0.9,
        )
        illustrative.move_to(at(AXIS_LEFT_X + AXIS_LENGTH / 2, AXIS_Y - 1.7))
        self.play(FadeIn(illustrative), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.15), run_time=3.0)
        self.wait(0.6)

        # The failure the zero-width dots show.
        zero_note = VGroup(
            Text("Zero width at 1.00 (red dots):", font_size=26, color=NM_PRIMARY, weight=BOLD),
            Text(
                f"all {N_SMALL} correct, so SE = 0 and the\n"
                "interval claims certainty, yet it\n"
                f"misses the true value {TRUE_ACCURACY_LABEL}",
                font_size=24,
                color=NM_TEXT,
                line_spacing=0.9,
            ),
        ).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        zero_note.move_to(at(3.75, 0.9))
        self.play(FadeIn(zero_note), run_time=0.7)
        self.wait(2.2)
        self.play(FadeOut(zero_note), run_time=0.5)

        # Measured numbers: the program's coverage over simulated evals.
        measured_title = Text("Measured coverage", font_size=30, color=NM_TEXT, weight=BOLD)
        measured_title.move_to(at(3.75, 2.55))
        measured_sub = Text(
            f"mu = {TRUE_ACCURACY_LABEL}, n = {N_SMALL}; {REPLICATES_LABEL} simulated evals\n"
            f"target coverage {TARGET_COVERAGE}",
            font_size=20,
            color=MUTED,
            line_spacing=0.9,
        )
        measured_sub.move_to(at(3.75, 1.8))
        table = stat_table(
            (
                ("CLT", COVERAGE_CLT),
                ("bootstrap", COVERAGE_BOOTSTRAP),
                ("Wilson", COVERAGE_WILSON),
                ("zero-width share", ZERO_WIDTH_SHARE),
            ),
            (NM_PRIMARY, NM_ORANGE, NM_GREEN, NM_PRIMARY),
            name_x=0.7,
            value_x=4.5,
            top_y=0.9,
            step=0.55,
            name_size=26,
            value_size=30,
        )
        table[3].shift(DOWN * 0.15)
        zero_detail = Text(
            f"(CLT and bootstrap; Wilson {ZERO_WIDTH_WILSON})",
            font_size=18,
            color=MUTED,
        )
        zero_detail.move_to(at(0.7, -1.35), aligned_edge=LEFT)
        self.play(FadeIn(measured_title), FadeIn(measured_sub), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(row) for row in table], lag_ratio=0.35), run_time=1.6)
        self.play(FadeIn(zero_detail), run_time=0.4)
        self.wait(1.5)

        caveat = Text(
            "Miller (arXiv 2411.00640, Sec. 2.1) applies\n"
            "the CLT to evals with “a large number of\n"
            "questions”. Small-n coverage and Wilson are\n"
            "this program's extension: Brown, Cai &\n"
            "DasGupta (2001), doi:10.1214/ss/1009213286",
            font_size=19,
            color=MUTED,
            line_spacing=0.9,
        )
        caveat.move_to(at(0.7, -2.6), aligned_edge=LEFT)
        self.play(FadeIn(caveat), run_time=0.7)
        self.wait(3.8)
        self.clear_all()

    def show_paired(self) -> None:
        """Same eval set, two models: the paired interval is narrower than the unpaired one."""
        header = Text("Same questions, two models: pair the scores", font_size=32, color=NM_TEXT)
        header.to_edge(UP, buff=0.4)
        sub = Text(
            f"model A (8 features) vs model B (7 features), n = {N_PAIRED} questions",
            font_size=22,
            color=MUTED,
        )
        sub.next_to(header, DOWN, buff=0.2)
        self.play(FadeIn(header), FadeIn(sub), run_time=0.7)

        caption = Text(
            f"{CONFIDENCE_LABEL} interval width for A − B",
            font_size=24,
            color=NM_TEXT,
        )
        caption.move_to(at(-3.6, 1.95))
        unpaired_bar = make_bar(WIDTH_UNPAIRED, WIDTH_UNPAIRED, 2.9, 1.2, NM_ORANGE, 26)
        paired_bar = make_bar(WIDTH_PAIRED, WIDTH_UNPAIRED, 2.9, 1.2, NM_GREEN, 26)
        bars = VGroup(unpaired_bar, paired_bar).arrange(RIGHT, buff=1.2, aligned_edge=DOWN)
        bars.move_to(at(-3.6, -0.3))
        unpaired_name = Text("unpaired", font_size=22, color=NM_TEXT)
        unpaired_name.next_to(unpaired_bar[0], DOWN, buff=0.15)
        paired_name = Text("paired", font_size=22, color=NM_TEXT)
        paired_name.next_to(paired_bar[0], DOWN, buff=0.15)
        self.play(FadeIn(caption), run_time=0.5)
        self.play(FadeIn(unpaired_bar, shift=UP * 0.3), FadeIn(unpaired_name), run_time=0.9)
        self.play(FadeIn(paired_bar, shift=UP * 0.3), FadeIn(paired_name), run_time=0.9)

        ratio = Text(
            f"paired / unpaired width = {WIDTH_RATIO}",
            font_size=22,
            color=NM_GREEN,
            weight=BOLD,
        )
        ratio.move_to(at(-3.6, -2.95))
        self.play(FadeIn(ratio), run_time=0.6)
        self.wait(0.8)

        facts = stat_table(
            (
                ("pool difference A − B", POOL_DIFFERENCE),
                ("Corr(s_A, s_B)", CORRELATION),
            ),
            (NM_TEXT, NM_YELLOW),
            name_x=0.7,
            value_x=5.0,
            top_y=1.85,
            step=0.6,
            name_size=24,
            value_size=28,
        )
        why = Text(
            "Scores are positively correlated: A and B\n"
            "tend to agree on easy and hard questions,\n"
            "so Var(A − B) is smaller than Var(s_A) +\n"
            "Var(s_B), the variance an unpaired\n"
            "interval assumes",
            font_size=21,
            color=NM_TEXT,
            line_spacing=0.9,
        )
        why.move_to(at(0.7, 0.1), aligned_edge=LEFT)
        self.play(LaggedStart(*[FadeIn(row) for row in facts], lag_ratio=0.4), run_time=1.2)
        self.play(FadeIn(why), run_time=0.7)
        self.wait(1.0)

        coverage_title = Text(
            f"coverage of the pool difference (target {TARGET_COVERAGE})",
            font_size=20,
            color=MUTED,
        )
        coverage_title.move_to(at(0.7, -1.2), aligned_edge=LEFT)
        coverage = stat_table(
            (("unpaired", COVERAGE_UNPAIRED), ("paired", COVERAGE_PAIRED)),
            (NM_ORANGE, NM_GREEN),
            name_x=0.7,
            value_x=3.0,
            top_y=-1.8,
            step=0.55,
            name_size=24,
            value_size=28,
        )
        coverage_note = Text(
            "unpaired over-covers (conservative);\npaired lands near the target",
            font_size=20,
            color=MUTED,
            line_spacing=0.9,
        )
        coverage_note.move_to(at(0.7, -3.2), aligned_edge=LEFT)
        self.play(FadeIn(coverage_title), run_time=0.5)
        self.play(FadeIn(coverage), FadeIn(coverage_note), run_time=0.8)
        self.wait(3.2)
        self.clear_all()

    def show_questions(self) -> None:
        """Minimum detectable effect against the question count, and Miller's worked example."""
        header = Text("How many questions does a difference need?", font_size=32, color=NM_TEXT)
        header.to_edge(UP, buff=0.4)
        self.play(FadeIn(header), run_time=0.6)

        legend = VGroup(
            Text("paired MDE (Miller Eq. 10)", font_size=20, color=NM_GREEN),
            Text("unpaired: this program's extension", font_size=20, color=MUTED),
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        legend.move_to(at(-6.9, 2.45), aligned_edge=LEFT)
        max_mde = max(unpaired for _, _, unpaired in MDE_ROWS)
        groups = VGroup()
        for n, paired, unpaired in MDE_ROWS:
            pair = VGroup(
                make_bar(paired, max_mde, 2.8, 0.7, NM_GREEN, 16),
                make_bar(unpaired, max_mde, 2.8, 0.7, MUTED, 16),
            ).arrange(RIGHT, buff=0.08, aligned_edge=DOWN)
            name = Text(f"n = {n}", font_size=20, color=NM_TEXT)
            name.next_to(pair, DOWN, buff=0.15)
            groups.add(VGroup(pair, name))
        groups.arrange(RIGHT, buff=0.35, aligned_edge=UP)
        groups.move_to(at(-3.4, -0.55))
        self.play(FadeIn(legend), run_time=0.5)
        self.play(
            LaggedStart(*[FadeIn(g, shift=UP * 0.2) for g in groups], lag_ratio=0.4),
            run_time=2.6,
        )
        mde_note = Text(
            f"minimum detectable effect, alpha = {ALPHA_LABEL}, beta = {BETA_LABEL}",
            font_size=20,
            color=MUTED,
        )
        mde_note.move_to(at(-3.4, -3.4))
        self.play(FadeIn(mde_note), run_time=0.5)
        self.wait(1.2)

        miller = VGroup(
            Text("Miller's worked example (Eq. 9)", font_size=26, color=NM_YELLOW, weight=BOLD),
            Text(
                f"omega² = {MILLER_OMEGA_SQUARED}, delta = {MILLER_DELTA}\n"
                f"alpha = {ALPHA_LABEL}, beta = {BETA_LABEL}",
                font_size=22,
                color=NM_TEXT,
                line_spacing=0.9,
            ),
            Text(f"n ≈ {MILLER_N} questions", font_size=38, color=NM_GREEN, weight=BOLD),
            Text("Miller calls these parameters fictional", font_size=20, color=MUTED),
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        miller.move_to(at(0.7, 1.0), aligned_edge=LEFT)
        self.play(LaggedStart(*[FadeIn(m) for m in miller], lag_ratio=0.45), run_time=2.2)
        self.wait(1.0)

        toy = VGroup(
            Text("This toy pool", font_size=24, color=NM_TEXT, weight=BOLD),
            Text(
                f"paired omega² = {OMEGA_SQUARED_PAIRED}\n"
                f"unpaired Var(s_A) + Var(s_B) = {VARIANCE_UNPAIRED}",
                font_size=20,
                color=NM_TEXT,
                line_spacing=0.9,
            ),
            Text(f"z = {Z_CRITICAL}, z_beta = {Z_BETA}", font_size=18, color=MUTED),
        ).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        toy.move_to(at(0.7, -1.9), aligned_edge=LEFT)
        self.play(FadeIn(toy), run_time=0.8)
        self.wait(3.6)
        self.clear_all()

    def show_limits(self) -> None:
        """What the toy does not show, in two readable screens."""
        header = Text("Limits", font_size=36, color=NM_PRIMARY)
        header.to_edge(UP, buff=0.4)
        first = bullet_list(
            (
                "Part A scores are binary with K = 1 answer per\nquestion; no clustering (Miller Sec. 2.2)",
                f"At n = {N_SMALL} the paired interval covered {PAIRED_COVERAGE_N30},\nbelow the {TARGET_COVERAGE} target",
                f"At mu = {TRUE_ACCURACY_LABEL}, n = {N_PAIRED}: bootstrap covered "
                f"{BOOTSTRAP_COVERAGE_N100},\nCLT {CLT_COVERAGE_N100}",
            ),
            font_size=26,
        ).move_to(DOWN * 0.3)
        self.play(FadeIn(header), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(item) for item in first], lag_ratio=0.4), run_time=2.0)
        self.wait(3.2)
        self.play(FadeOut(first), run_time=0.5)
        second = bullet_list(
            (
                "Toy synthetic arms, not real LLM evals; one\nseed (42) on one host",
                "Unpaired MDE rows extend Eq. 10; Miller's\nexample parameters are fictional (his words)",
                "Numbers come from the pinned default run\n(seed 42, CPython 3.12.8)",
            ),
            font_size=26,
        ).move_to(DOWN * 0.3)
        self.play(LaggedStart(*[FadeIn(item) for item in second], lag_ratio=0.4), run_time=2.0)
        self.wait(3.2)
        self.play(FadeOut(second), FadeOut(header), run_time=0.6)
