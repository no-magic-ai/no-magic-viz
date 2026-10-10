"""
Scene: Green-List Watermarking
Script: microwatermark.py
Description: A keyed green list biases sampling; a z-test finds it, except where text leaves no room
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

# A muted gray for captions, a soft red for non-green tokens, and a blue that reads on the
# dark background.
MUTED = "#8a8aa8"
RED_TOKEN = "#c0607a"
LIGHT_BLUE = "#4fa3e0"

# Every number shown below is copied from the default run of no-magic's
# 03-systems/microwatermark.py (seed 42, CPython 3.12.8). Logit bars in the first
# section are schematic (heights encode no values); every other bar height is
# proportional to the printed value it is labeled with.
GAMMA = "0.25"
DELTA = "2.0"
# Gate E1: a constructed text with 36 scored pairs, 28 of them green.
E1_SCORED, E1_GREEN, E1_Z = 36, 28, "7.3131"
# "median-z" example texts (sample idx 111, generation key 1): first 12 generated tokens of the
# watermarked text and of the unwatermarked text from the same prompt and random stream.
# True = starred (green) in the program's output; the first token is never scored.
WM_TOKENS = (
    ("horse", False),
    ("green", True),
    ("horse", True),
    ("sees", False),
    ("a", True),
    ("young", True),
    ("horse", False),
    ("again", False),
    ("and", True),
    ("a", False),
    ("horse", False),
    ("follows", True),
)
PLAIN_TOKENS = (
    ("horse", False),
    ("red", False),
    ("mouse", False),
    ("sees", False),
    ("the", False),
    ("old", False),
    ("owl", True),
    (".", False),
    ("the", True),
    ("horse", False),
    ("today", True),
    ("and", False),
)
WM_Z200 = ("10.19", "7.04")  # (PLAIN, DEDUP) at 200 generated tokens
PLAIN_Z200 = ("-0.78", "0.10")
# The same watermarked text, tokens 15-21: the near-deterministic opener stays red.
OPENER_TOKENS = (
    ("today", True),
    (".", True),
    ("once", False),
    ("upon", False),
    ("a", False),
    ("time", False),
    (",", True),
)
# DEDUP rate(z > 4) at 200 tokens: right key (200 texts), then controls scored with 200 null
# keys (40,000 (text, key) pairs each).
DEDUP_RATES = (
    ("right key", 0.9700, "0.970"),
    ("wrong key", 0.0, "0.00000"),
    ("unwatermarked", 0.00003, "0.00003"),
    ("grammar text", 0.0, "0.00000"),
)
# DEDUP right-key rate(z > 4) by generated length.
LENGTH_RATES = ((16, 0.1350), (32, 0.3350), (64, 0.6500), (128, 0.9200), (200, 0.9700))
# Repetitive control (unwatermarked, t = 0.3), 200 tokens, 40,000 pairs.
REP_PLAIN_SD, REP_PLAIN_RATE = 2.906, "0.08060"
REP_DEDUP_SD, REP_DEDUP_RATE = 0.952, "0 events"
# Model text t = 1 under null keys, 200 tokens.
T1_PLAIN_RATE, T1_DEDUP_RATE = "0.01087", "0.00003"
# Gate W6b: observed green fraction by model-entropy bucket (primary arm).
BUCKETS = (("low", 0.340), ("mid", 0.455), ("high", 0.655))
# Gate W10 and the report-only before-temperature arm: DEDUP rate at 200 tokens.
TEMPERATURE_RATES = (
    ("t = 1", 0.970, "0.970"),
    ("t = 0.3, +δ after", 0.110, "0.110"),
    ("t = 0.3, +δ before", 0.980, "0.980"),
)
PPL_RATIO_SOFT, PPL_RATIO_HARD = "1.241", "2.537"


def token_strip(
    tokens: tuple[tuple[str, bool], ...],
    font_size: int = 18,
    neutral: bool = False,
    starts_text: bool = True,
) -> VGroup:
    """Tokens in boxes. Scored tokens: green filled or red outlined.

    starts_text=True marks the first box as the unscored first generated token; neutral=True
    draws plain boxes for tokens whose color the scene does not claim.
    """
    boxes = VGroup()
    for i, (word, green) in enumerate(tokens):
        color = MUTED if neutral else NM_GREEN if green else RED_TOKEN
        label = Text(word, font_size=font_size, color=NM_TEXT)
        box = SurroundingRectangle(label, buff=0.08, color=color, stroke_width=1.6)
        if green and not neutral:
            box.set_fill(NM_GREEN, opacity=0.35)
        if i == 0 and starts_text and not neutral:
            box.set_stroke(MUTED, width=1.2)
        boxes.add(VGroup(box, label))
    boxes.arrange(RIGHT, buff=0.1)
    return boxes


def rate_bars(
    rows: tuple[tuple[str, float, str], ...], colors: tuple[str, ...], max_height: float
) -> VGroup:
    """One bar per row; height proportional to the printed rate, label above, name below."""
    bars = VGroup()
    for (name, value, label), color in zip(rows, colors):
        bar = Rectangle(width=0.7, height=max(value * max_height, 0.04), color=color)
        bar.set_fill(color, opacity=0.8)
        value_text = Text(label, font_size=18, color=NM_TEXT)
        name_text = Text(name, font_size=16, color=MUTED)
        bars.add(VGroup(bar, value_text, name_text))
    bars.arrange(RIGHT, buff=0.75, aligned_edge=DOWN)
    for group in bars:
        group[1].next_to(group[0], UP, buff=0.08)
        group[2].next_to(group[0], DOWN, buff=0.12)
    return bars


def gaussian_curve(sd: float, color: str, x_scale: float, height: float) -> VMobject:
    """A normal-shaped curve with the printed standard deviation (shape schematic)."""
    curve = FunctionGraph(
        lambda x: height * math.exp(-0.5 * (x / (sd * x_scale)) ** 2),
        x_range=(-4.5, 4.5, 0.05),
        color=color,
    )
    return curve


class WatermarkScene(NoMagicScene):
    title_text = "Green-List Watermarking"
    subtitle_text = "A keyed logit bias at sampling time, a z-test that needs no model"

    def animate(self) -> None:
        self.show_sampling_step()
        self.show_detector()
        self.show_controls()
        self.show_repetition()
        self.show_low_entropy()
        self.show_limits()

    def clear_all(self, run_time: float = 0.6) -> None:
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)

    def show_sampling_step(self) -> None:
        """Trained logits -> keyed green list of the previous token -> +delta -> sample."""
        header = Text(
            "One sampling step: keyed green list, then +δ",
            font_size=28,
            color=NM_TEXT,
            weight=BOLD,
        )
        header.to_edge(UP, buff=0.4)
        context = token_strip((("the", False), ("young", False)), font_size=20, neutral=True)
        context.move_to(LEFT * 4.6 + UP * 1.7)
        context_label = Text("previous tokens", font_size=16, color=MUTED)
        context_label.next_to(context, DOWN, buff=0.15)
        self.play(FadeIn(header), FadeIn(context), FadeIn(context_label), run_time=0.8)

        hash_box = VGroup(
            Text("blake2b(previous token, key K)", font_size=18, color=NM_YELLOW),
            Text("→ seed → 12 of 48 tokens are green", font_size=18, color=NM_YELLOW),
            Text(f"γ = {GAMMA}, a fresh list at every step", font_size=16, color=MUTED),
        ).arrange(DOWN, buff=0.1)
        hash_box.move_to(RIGHT * 2.2 + UP * 1.7)
        hash_frame = SurroundingRectangle(hash_box, color=NM_YELLOW, buff=0.15)
        hash_arrow = Arrow(context.get_right(), hash_frame.get_left(), buff=0.15, color=NM_TEXT)
        self.play(GrowArrow(hash_arrow), FadeIn(hash_box), Create(hash_frame), run_time=1.0)

        # Schematic logits for 12 candidate tokens; every third is green.
        heights = (1.1, 0.5, 0.9, 1.4, 0.3, 0.7, 1.0, 0.4, 0.8, 0.6, 0.35, 0.55)
        greens = tuple(i % 3 == 1 for i in range(len(heights)))
        bars = VGroup()
        for h, green in zip(heights, greens):
            color = NM_GREEN if green else RED_TOKEN
            bar = Rectangle(width=0.32, height=h, color=color)
            bar.set_fill(color, opacity=0.7)
            bars.add(bar)
        bars.arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
        bars.move_to(LEFT * 2.0 + DOWN * 1.4)
        bars_label = Text("trained model's logits (schematic)", font_size=16, color=MUTED)
        bars_label.next_to(bars, DOWN, buff=0.15)
        self.play(FadeIn(bars), FadeIn(bars_label), run_time=0.8)

        # Keep a faint outline of the original logits so the +delta lift stays visible.
        ghost = bars.copy()
        ghost.set_fill(opacity=0.0)
        ghost.set_stroke(opacity=0.35)
        self.add(ghost)
        boosted = bars.copy()
        for boosted_bar, green in zip(boosted, greens):
            if green:
                boosted_bar.stretch_to_fit_height(boosted_bar.height + 0.6, about_edge=DOWN)
        plus = Text(f"+δ = {DELTA} on green logits", font_size=18, color=NM_GREEN)
        plus.next_to(bars, UP, buff=0.75)
        self.play(Transform(bars, boosted), FadeIn(plus), run_time=1.0)

        formulas = VGroup(
            Text("p̂ᵢ ∝ exp(lᵢ + δ·1[i ∈ G])", font_size=20, color=NM_TEXT),
            Text("P(green) = αg / (αg + 1 − g),  α = e^δ", font_size=20, color=NM_TEXT),
            Text("g = the model's own mass on G", font_size=16, color=MUTED),
        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        formulas.move_to(RIGHT * 3.6 + DOWN * 1.2)
        self.play(FadeIn(formulas), run_time=0.9)
        pick = SurroundingRectangle(bars[10], color=NM_GREEN, buff=0.06)
        sampled = Text("sampled", font_size=16, color=NM_GREEN)
        sampled.next_to(pick, UP, buff=0.1)
        self.play(Create(pick), FadeIn(sampled), run_time=0.6)
        self.wait(1.8)
        self.clear_all()

    def show_detector(self) -> None:
        """The detector rebuilds each green list from the text and the key, then counts."""
        header = Text(
            "Detector: count green pairs, no model needed",
            font_size=28,
            color=NM_TEXT,
            weight=BOLD,
        )
        header.to_edge(UP, buff=0.4)
        wm = token_strip(WM_TOKENS, font_size=16)
        plain = token_strip(PLAIN_TOKENS, font_size=16)
        wm_label = Text("watermarked (key 1)", font_size=16, color=NM_GREEN)
        plain_label = Text("same prompt and stream, no watermark", font_size=16, color=MUTED)
        wm.move_to(UP * 1.6)
        wm_label.next_to(wm, UP, buff=0.12)
        plain.move_to(UP * 0.35)
        plain_label.next_to(plain, UP, buff=0.12)
        self.play(FadeIn(header), FadeIn(wm), FadeIn(wm_label), run_time=0.9)
        self.play(FadeIn(plain), FadeIn(plain_label), run_time=0.8)

        formula = Text("z = (|s|_G − γT) / √(T·γ(1 − γ))   (Eq. 3)", font_size=22, color=NM_YELLOW)
        formula.move_to(DOWN * 0.85)
        note = Text(
            "T = scored pairs: the first token's list needs the unseen prompt",
            font_size=15,
            color=MUTED,
        )
        note.next_to(formula, DOWN, buff=0.12)
        key_note = Text(
            "filled = green after its previous token under key 1; gray = first token, not scored",
            font_size=14,
            color=MUTED,
        )
        key_note.next_to(plain, DOWN, buff=0.18)
        self.play(FadeIn(formula), FadeIn(note), FadeIn(key_note), run_time=0.8)

        e1 = Text(
            f"gate E1: ({E1_GREEN} − 0.25·{E1_SCORED}) / √({E1_SCORED}·0.25·0.75) = {E1_Z}",
            font_size=17,
            color=NM_TEXT,
        )
        z_line = Text(
            f"these texts at 200 tokens, PLAIN / DEDUP:  {WM_Z200[0]} / {WM_Z200[1]}"
            f"   vs   {PLAIN_Z200[0]} / {PLAIN_Z200[1]}",
            font_size=17,
            color=NM_GREEN,
        )
        lines = VGroup(e1, z_line).arrange(DOWN, buff=0.15)
        lines.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(e1), run_time=0.6)
        self.play(FadeIn(z_line), run_time=0.6)
        self.wait(2.0)
        self.clear_all()

    def show_controls(self) -> None:
        """Right key against wrong keys and unwatermarked text, then power by length."""
        header = Text("DEDUP rate(z > 4) at 200 tokens", font_size=28, color=NM_TEXT, weight=BOLD)
        header.to_edge(UP, buff=0.4)
        bars = rate_bars(DEDUP_RATES, (NM_GREEN, NM_ORANGE, NM_PURPLE, LIGHT_BLUE), 2.4)
        bars.move_to(LEFT * 2.6 + DOWN * 0.3)
        caption = Text(
            "controls: 200 texts × 200 null keys = 40,000 pairs each",
            font_size=15,
            color=MUTED,
        )
        caption.next_to(bars, DOWN, buff=0.55)
        self.play(FadeIn(header), run_time=0.5)
        self.play(FadeIn(bars), FadeIn(caption), run_time=1.0)

        axes_title = Text("right key, by length", font_size=18, color=NM_TEXT)
        points = VGroup()
        for length, rate in LENGTH_RATES:
            bar = Rectangle(width=0.36, height=max(rate * 2.4, 0.04), color=NM_GREEN)
            bar.set_fill(NM_GREEN, opacity=0.6)
            value = Text(f"{rate:.3f}", font_size=14, color=NM_TEXT)
            name = Text(str(length), font_size=14, color=MUTED)
            points.add(VGroup(bar, value, name))
        points.arrange(RIGHT, buff=0.22, aligned_edge=DOWN)
        for group in points:
            group[1].next_to(group[0], UP, buff=0.06)
            group[2].next_to(group[0], DOWN, buff=0.08)
        points.move_to(RIGHT * 3.7 + DOWN * 0.3)
        axes_title.next_to(points, UP, buff=0.5)
        tokens_label = Text("generated tokens", font_size=14, color=MUTED)
        tokens_label.next_to(points, DOWN, buff=0.35)
        self.play(FadeIn(points), FadeIn(axes_title), FadeIn(tokens_label), run_time=1.0)
        note = Text(
            "short texts are weak evidence; a wrong key sees nothing",
            font_size=17,
            color=NM_YELLOW,
        )
        note.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(2.0)
        self.clear_all()

    def show_repetition(self) -> None:
        """Repeated pairs reuse one coin: PLAIN's null spreads out, DEDUP's does not."""
        header = Text(
            "Repeated pairs break PLAIN's calibration",
            font_size=28,
            color=NM_TEXT,
            weight=BOLD,
        )
        header.to_edge(UP, buff=0.4)
        alt = token_strip(
            tuple((w, False) for w in ("green", "old", "green", "old", "green", "old")),
            font_size=18,
            neutral=True,
        )
        alt.move_to(UP * 1.75)
        alt_note = Text(
            "gate E8: 5 scored pairs for PLAIN, 2 distinct pairs for DEDUP",
            font_size=16,
            color=MUTED,
        )
        alt_note.next_to(alt, DOWN, buff=0.15)
        self.play(FadeIn(header), FadeIn(alt), FadeIn(alt_note), run_time=0.9)

        axis = Line(LEFT * 4.5, RIGHT * 4.5, color=NM_GRID).shift(DOWN * 1.6)
        # Equal areas: a normal curve's peak height is proportional to 1 / sd.
        peak = 2.2 * REP_DEDUP_SD
        plain_curve = gaussian_curve(REP_PLAIN_SD, NM_PRIMARY, 0.42, peak / REP_PLAIN_SD)
        dedup_curve = gaussian_curve(REP_DEDUP_SD, NM_GREEN, 0.42, peak / REP_DEDUP_SD)
        plain_curve.shift(DOWN * 1.6)
        dedup_curve.shift(DOWN * 1.6)
        threshold = DashedLine(UP * 0.9, DOWN * 1.6, color=NM_YELLOW).shift(RIGHT * 4 * 0.42)
        threshold_label = Text("z = 4", font_size=14, color=NM_YELLOW)
        threshold_label.next_to(threshold, UP, buff=0.05)
        self.play(Create(axis), Create(dedup_curve), Create(plain_curve), run_time=1.2)
        self.play(Create(threshold), FadeIn(threshold_label), run_time=0.5)
        legend = VGroup(
            Text(
                f"PLAIN sd {REP_PLAIN_SD:.3f}, rate(z>4) {REP_PLAIN_RATE}",
                font_size=16,
                color=NM_PRIMARY,
            ),
            Text(
                f"DEDUP sd {REP_DEDUP_SD:.3f}, {REP_DEDUP_RATE} above 4",
                font_size=16,
                color=NM_GREEN,
            ),
            Text(
                "unwatermarked t = 0.3 text, 40,000 null pairs (curves: normal shape, printed sd)",
                font_size=13,
                color=MUTED,
            ),
            Text(
                f"t = 1 model text: PLAIN {T1_PLAIN_RATE} vs DEDUP {T1_DEDUP_RATE}",
                font_size=15,
                color=NM_TEXT,
            ),
        ).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        legend.next_to(axis, DOWN, buff=0.3)
        self.play(FadeIn(legend), run_time=0.8)
        self.wait(2.2)
        self.clear_all()

    def show_low_entropy(self) -> None:
        """Where the model is sure, the bias cannot pick the token: low entropy, low signal."""
        header = Text(
            "Low entropy leaves the watermark no room",
            font_size=28,
            color=NM_TEXT,
            weight=BOLD,
        )
        header.to_edge(UP, buff=0.4)
        opener = token_strip(OPENER_TOKENS, font_size=18, starts_text=False)
        opener.move_to(UP * 1.75)
        opener_note = Text(
            "same watermarked text: the fixed opener 'once upon a time' stays red",
            font_size=15,
            color=MUTED,
        )
        opener_note.next_to(opener, DOWN, buff=0.15)
        self.play(FadeIn(header), FadeIn(opener), FadeIn(opener_note), run_time=0.9)

        bucket_rows = tuple((f"{name} entropy", v, f"{v:.3f}") for name, v in BUCKETS)
        buckets = rate_bars(bucket_rows, (MUTED, LIGHT_BLUE, NM_GREEN), 2.0)
        buckets.move_to(LEFT * 3.4 + DOWN * 1.0)
        buckets_title = Text("green fraction (gate W6b), γ = 0.25", font_size=16, color=NM_TEXT)
        buckets_title.next_to(buckets, UP, buff=0.35)
        self.play(FadeIn(buckets), FadeIn(buckets_title), run_time=0.9)

        temps = rate_bars(TEMPERATURE_RATES, (NM_GREEN, NM_PRIMARY, NM_ORANGE), 2.0)
        temps.move_to(RIGHT * 3.0 + DOWN * 1.0)
        temps_title = Text("DEDUP rate(z>4), 200 tokens", font_size=16, color=NM_TEXT)
        temps_title.next_to(temps, UP, buff=0.35)
        self.play(FadeIn(temps), FadeIn(temps_title), run_time=0.9)
        note = Text(
            "sharper sampling (t = 0.3) weakens it; adding δ before t is a report-only arm",
            font_size=15,
            color=NM_YELLOW,
        )
        note.to_edge(DOWN, buff=0.25)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(2.2)
        self.clear_all()

    def show_limits(self) -> None:
        """What the toy shows and what it does not."""
        header = Text("What this toy does not show", font_size=28, color=NM_TEXT, weight=BOLD)
        header.to_edge(UP, buff=0.45)
        items = VGroup(
            Text(
                f"quality cost: perplexity ×{PPL_RATIO_SOFT} (soft) vs ×{PPL_RATIO_HARD} (hard rule)",
                font_size=18,
                color=NM_TEXT,
            ),
            Text(
                "48-word toy grammar, hash of 1 previous token, public demo keys",
                font_size=18,
                color=NM_TEXT,
            ),
            Text(
                "gates set after a first look at the same seeded data: a consistency check",
                font_size=18,
                color=NM_TEXT,
            ),
            Text(
                "Theorem 4.2 check is non-tight except in near-deterministic contexts",
                font_size=18,
                color=NM_TEXT,
            ),
            Text(
                "no attack tested: no robustness, security or real-text claim",
                font_size=18,
                color=NM_PRIMARY,
            ),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        items.next_to(header, DOWN, buff=0.55)
        self.play(FadeIn(header), run_time=0.5)
        for item in items:
            self.play(FadeIn(item, shift=RIGHT * 0.2), run_time=0.45)
        self.wait(2.4)
        self.clear_all(run_time=0.8)
