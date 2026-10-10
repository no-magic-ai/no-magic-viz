"""
Scene: Reasoning Traces and Self-Consistency
Script: microcot.py
Description: A tiny model writes its own reasoning traces; sampling several and voting beats one
greedy trace, partly by undoing greedy's poor route choice
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import (
    NM_BLUE,
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

# A muted gray for captions, a soft red for wrong values and claims not made, and a blue that
# reads on the dark background.
MUTED = "#8a8aa8"
WRONG = "#c0607a"
LIGHT_BLUE = "#4fa3e0"

# Provenance. Every model output and accuracy below is copied from the frozen, pre-registered S3
# design-study run of the program this scene illustrates (no-magic 03-systems/microcot.py; seed
# 42, CPython 3.12.8; reference stdout SHA-256
# bd4614398dcf87248ed626cf30ec985e6d7b263f14b740a35c5eeb86b78fd480). The shipped program must
# reproduce these values exactly; that reproduction is checked by independent qualification,
# not by this scene. Differences shown (+0.104, +0.068) are plain arithmetic on the displayed
# values. The three routes of 3+7+2+9 are the task's own arithmetic, not model output, and the
# model diagram is schematic. Bar and curve heights are proportional to the printed accuracies.
N_PARAMS = "17,345"
# Sampled traces printed by the run's inspection section for the first and third test problems
# (four samples each, drawn from the separate inspection stream, not the 40-sample vote).
PROMPT_A, ANSWER_A = "3+1+4+7=", 5
SAMPLES_A = (("L485#5.", 5), ("L485#5.", 5), ("R125#5.", 5), ("R103#3.", 3))
PROMPT_B, ANSWER_B = "2+7+3+6=", 8
SAMPLES_B = (("R960#0.", 0), ("L922#2.", 2), ("T998#8.", 8), ("L920#0.", 0))
# Test-slice accuracies (500 problems).
ACCURACY_BARS = (
    ("direct\ngreedy", 0.650, "0.650"),
    ("trace\ngreedy", 0.702, "0.702"),
    ("one sample\nτ = 0.7", 0.639, "0.639"),
    ("best route L\n(post hoc)", 0.738, "0.738"),
    ("vote\nk = 40", 0.806, "0.806"),
)
VOTE_BY_K = ((1, 0.646), (5, 0.748), (10, 0.786), (20, 0.810), (40, 0.806))
GREEDY_ACC = 0.702


def trace_tokens(trace: str, font_size: int = 28) -> VGroup:
    """One colored glyph per trace token: route, partial sums, '#', answer, end."""
    colors = {"L": NM_YELLOW, "R": NM_ORANGE, "T": NM_PURPLE, "#": NM_PRIMARY, ".": MUTED}
    glyphs = VGroup()
    for i, ch in enumerate(trace):
        color = colors.get(ch, NM_TEXT)
        if i == 5:
            color = NM_GREEN  # the answer digit the parser reads
        glyphs.add(Text(ch, font_size=font_size, color=color, font="Monospace"))
    glyphs.arrange(RIGHT, buff=0.06)
    return glyphs


def accuracy_bars(
    rows: tuple[tuple[str, float, str], ...], colors: tuple[str, ...], max_height: float
) -> VGroup:
    """One bar per row; height proportional to the printed accuracy, value above, name below."""
    bars = VGroup()
    for (name, value, label), color in zip(rows, colors):
        bar = Rectangle(width=1.0, height=value * max_height, color=color)
        bar.set_fill(color, opacity=0.8)
        value_text = Text(label, font_size=24, color=NM_TEXT)
        name_text = Text(name, font_size=20, color=NM_TEXT, line_spacing=0.8)
        bars.add(VGroup(bar, value_text, name_text))
    bars.arrange(RIGHT, buff=0.45, aligned_edge=DOWN)
    for group in bars:
        group[1].next_to(group[0], UP, buff=0.08)
        group[2].next_to(group[0], DOWN, buff=0.12)
    return bars


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


class CoTScene(NoMagicScene):
    title_text = "Reasoning Traces & Self-Consistency"
    subtitle_text = "Sample several model-written traces, parse each answer, vote"

    def animate(self) -> None:
        self.show_task()
        self.show_model()
        self.show_sample_parse_vote()
        self.show_results()
        self.show_vote_by_k()
        self.show_limits()

    def clear_all(self, run_time: float = 0.6) -> None:
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)

    def show_task(self) -> None:
        """Same problems, two training targets: answer directly, or write a route first."""
        header = Text("Two arms, one task: sum of 4 digits mod 10", font_size=34, color=NM_TEXT)
        header.to_edge(UP, buff=0.4)
        prompt = Text("3+7+2+9=", font_size=38, color=NM_TEXT, font="Monospace")
        prompt.move_to(LEFT * 4.8 + UP * 0.9)
        self.play(FadeIn(header), FadeIn(prompt), run_time=0.8)

        direct = VGroup(
            Text("direct arm:", font_size=26, color=LIGHT_BLUE),
            Text("1.", font_size=32, color=NM_GREEN, font="Monospace"),
        ).arrange(RIGHT, buff=0.3)
        direct.move_to(RIGHT * 0.6 + UP * 2.0)
        direct_arrow = Arrow(prompt.get_right(), direct.get_left(), buff=0.2, color=LIGHT_BLUE)
        self.play(GrowArrow(direct_arrow), FadeIn(direct), run_time=0.8)

        # The three routes are the task's own arithmetic (all mod 10), used as training targets.
        routes = VGroup(
            VGroup(trace_tokens("L021#1."), Text("(3+7) +2 +9", font_size=22, color=MUTED)),
            VGroup(trace_tokens("R181#1."), Text("(9+2) +7 +3", font_size=22, color=MUTED)),
            VGroup(trace_tokens("T011#1."), Text("(3+7)+(2+9)", font_size=22, color=MUTED)),
        )
        for route in routes:
            route.arrange(RIGHT, buff=0.45)
        routes.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        routes.move_to(RIGHT * 2.0 + DOWN * 0.55)
        trace_label = Text("trace arm: route p1 p2 p3 # answer", font_size=26, color=NM_YELLOW)
        trace_label.next_to(routes, UP, buff=0.3)
        trace_arrow = Arrow(prompt.get_right(), routes.get_left(), buff=0.2, color=NM_YELLOW)
        self.play(GrowArrow(trace_arrow), FadeIn(trace_label), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(r) for r in routes], lag_ratio=0.3), run_time=1.5)

        note = Text(
            "Decoders see only the prompt: every trace they print is model-written",
            font_size=24,
            color=NM_TEXT,
        )
        note.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(2.4)
        self.clear_all()

    def show_model(self) -> None:
        """The position-slot MLP both arms share, from one initialization."""
        header = Text(
            f"One tiny model, trained twice ({N_PARAMS} parameters)", font_size=32, color=NM_TEXT
        )
        header.to_edge(UP, buff=0.4)
        self.play(FadeIn(header), run_time=0.6)

        tokens = VGroup(
            *[
                Square(side_length=0.5, color=NM_GRID).set_fill(NM_BLUE, opacity=0.6)
                for _ in range(8)
            ]
        ).arrange(RIGHT, buff=0.08)
        token_text = VGroup(
            *[Text(ch, font_size=24, color=NM_TEXT, font="Monospace") for ch in "3+7+2+9="]
        )
        for square, glyph in zip(tokens, token_text):
            glyph.move_to(square)
        slots = VGroup(tokens, token_text)
        slots.move_to(LEFT * 3.7 + UP * 1.1)
        slot_label = Text("one table per position", font_size=22, color=MUTED)
        slot_label.next_to(slots, DOWN, buff=0.15)
        self.play(FadeIn(slots), FadeIn(slot_label), run_time=0.8)

        hidden = RoundedRectangle(width=2.3, height=0.85, corner_radius=0.15, color=NM_GREEN)
        hidden_text = Text("tanh, 48", font_size=26, color=NM_GREEN)
        hidden_text.move_to(hidden)
        hidden_group = VGroup(hidden, hidden_text).move_to(RIGHT * 1.5 + UP * 1.1)
        out = RoundedRectangle(width=2.6, height=0.85, corner_radius=0.15, color=NM_YELLOW)
        out_text = Text("softmax, 17", font_size=26, color=NM_YELLOW)
        out_text.move_to(out)
        out_group = VGroup(out, out_text).move_to(RIGHT * 4.9 + UP * 1.1)
        a1 = Arrow(slots.get_right(), hidden_group.get_left(), buff=0.15, color=NM_TEXT)
        a2 = Arrow(hidden_group.get_right(), out_group.get_left(), buff=0.15, color=NM_TEXT)
        self.play(GrowArrow(a1), FadeIn(hidden_group), run_time=0.7)
        self.play(GrowArrow(a2), FadeIn(out_group), run_time=0.7)

        equations = VGroup(
            Text("z_t = b1 + Q[t] + sum over s < t of E[s][x_s]", font_size=28, color=NM_TEXT),
            Text("p(x_t | x_<t) = softmax(W2 tanh(z_t) + b2)", font_size=28, color=NM_TEXT),
            Text(
                "Loss on completion tokens only; hand-written gradients; no attention",
                font_size=22,
                color=MUTED,
            ),
        ).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        equations.move_to(DOWN * 1.6)
        self.play(FadeIn(equations), run_time=1.0)
        self.wait(2.6)
        self.clear_all()

    def vote_column(self, prompt: str, samples: tuple[tuple[str, int], ...]) -> VGroup:
        """Model-written samples with their parsed answers."""
        rows = VGroup()
        for trace, answer in samples:
            parsed = Text(f"→ {answer}", font_size=26, color=NM_GREEN)
            rows.add(VGroup(trace_tokens(trace, font_size=26), parsed).arrange(RIGHT, buff=0.3))
        rows.arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        title = Text(prompt, font_size=30, color=NM_TEXT, font="Monospace")
        title.next_to(rows, UP, buff=0.3)
        return VGroup(title, rows)

    def show_sample_parse_vote(self) -> None:
        """Sample traces at temperature 0.7, read the digit after '#', count."""
        header = Text("Self-consistency: sample → parse → vote", font_size=34, color=NM_TEXT)
        header.to_edge(UP, buff=0.35)
        caption = Text(
            "4 printed samples at τ = 0.7 (the program votes over 40)", font_size=22, color=MUTED
        )
        caption.next_to(header, DOWN, buff=0.2)
        self.play(FadeIn(header), FadeIn(caption), run_time=0.6)

        column_a = self.vote_column(PROMPT_A, SAMPLES_A)
        column_a.move_to(LEFT * 3.4 + UP * 0.1)
        column_b = self.vote_column(PROMPT_B, SAMPLES_B)
        column_b.move_to(RIGHT * 3.0 + UP * 0.1)
        self.play(FadeIn(column_a[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(r) for r in column_a[1]], lag_ratio=0.3), run_time=1.6)
        # R103#3: the second partial sum is wrong (1 + 1 = 2, not 0) and the error propagates.
        wrong = SurroundingRectangle(column_a[1][3][0][2], color=WRONG, buff=0.05)
        wrong_label = Text("wrong step", font_size=20, color=WRONG)
        wrong_label.next_to(column_a[1][3], RIGHT, buff=0.3)
        self.play(Create(wrong), FadeIn(wrong_label), run_time=0.6)
        tally_a = Text(f"votes 5,5,5,3 → 5 (gold {ANSWER_A})", font_size=24, color=NM_GREEN)
        tally_a.next_to(column_a, DOWN, buff=0.3)
        self.play(FadeIn(tally_a), run_time=0.6)

        self.play(FadeIn(column_b[0]), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(r) for r in column_b[1]], lag_ratio=0.3), run_time=1.6)
        tally_b = Text(f"votes 0,2,8,0 → 0, wrong (gold {ANSWER_B})", font_size=24, color=WRONG)
        tally_b.next_to(column_b, DOWN, buff=0.3)
        self.play(FadeIn(tally_b), run_time=0.6)

        rules = VGroup(
            Text("vote = the most common parsed answer", font_size=26, color=NM_TEXT),
            Text(
                "tie: higher Eq. 1 weight, then smaller digit; none parses: abstain (wrong)",
                font_size=22,
                color=MUTED,
            ),
        ).arrange(DOWN, buff=0.12)
        rules.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(rules), run_time=0.8)
        self.wait(2.8)
        self.clear_all()

    def show_results(self) -> None:
        """Test-slice accuracies: the vote against greedy, single samples and the best route."""
        header = Text("500 held-out problems, seed 42", font_size=32, color=NM_TEXT)
        header.to_edge(UP, buff=0.3)
        source = Text(
            "frozen design values; the program must reproduce them exactly",
            font_size=20,
            color=MUTED,
        )
        source.next_to(header, DOWN, buff=0.12)
        self.play(FadeIn(header), FadeIn(source), run_time=0.6)

        colors = (LIGHT_BLUE, NM_YELLOW, NM_ORANGE, NM_PURPLE, NM_GREEN)
        bars = accuracy_bars(ACCURACY_BARS, colors, max_height=3.4)
        bars.move_to(LEFT * 2.6 + DOWN * 0.5)
        self.play(
            LaggedStart(*[GrowFromEdge(g[0], DOWN) for g in bars], lag_ratio=0.2),
            *[FadeIn(g[1]) for g in bars],
            *[FadeIn(g[2]) for g in bars],
            run_time=2.0,
        )
        notes = VGroup(
            Text("vote − greedy", font_size=24, color=NM_GREEN),
            Text("+0.104, p = 8.5e-09", font_size=24, color=NM_GREEN),
            Text("vote − best route", font_size=24, color=NM_PURPLE),
            Text("+0.068 (post hoc)", font_size=24, color=NM_PURPLE),
            Text("trace − direct", font_size=24, color=WRONG),
            Text("+0.052, p = 0.083:", font_size=24, color=WRONG),
            Text("not claimed", font_size=24, color=WRONG),
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        notes[2].shift(DOWN * 0.2)
        notes[3].shift(DOWN * 0.2)
        notes[4:].shift(DOWN * 0.4)
        notes.to_edge(RIGHT, buff=0.45).shift(DOWN * 0.3)
        self.play(FadeIn(notes[0:2]), run_time=0.7)
        self.wait(0.9)
        self.play(FadeIn(notes[2:4]), run_time=0.7)
        self.wait(0.9)
        self.play(FadeIn(notes[4:]), run_time=0.6)
        self.wait(2.8)
        self.clear_all()

    def show_vote_by_k(self) -> None:
        """More samples help, then saturate: vote accuracy by k against the greedy line."""
        header = Text("Vote accuracy by number of samples k", font_size=32, color=NM_TEXT)
        header.to_edge(UP, buff=0.4)
        self.play(FadeIn(header), run_time=0.6)

        axes = Axes(
            x_range=(0, 4.5, 1),
            y_range=(0.6, 0.85, 0.05),
            x_length=8.5,
            y_length=4.0,
            axis_config={"color": MUTED, "include_tip": False},
        )
        axes.move_to(DOWN * 0.35)
        y_labels = VGroup()
        for tick in (0.6, 0.7, 0.8):
            tick_label = Text(f"{tick:.1f}", font_size=22, color=MUTED)
            tick_label.next_to(axes.c2p(0, tick), LEFT, buff=0.15)
            y_labels.add(tick_label)
        x_labels = VGroup()
        points = []
        for i, (k, acc) in enumerate(VOTE_BY_K):
            x = i + 0.5
            label = Text(f"k={k}", font_size=22, color=NM_TEXT)
            label.next_to(axes.c2p(x, 0.6), DOWN, buff=0.2)
            x_labels.add(label)
            points.append(axes.c2p(x, acc))
        greedy_line = DashedLine(
            axes.c2p(0, GREEDY_ACC), axes.c2p(4.5, GREEDY_ACC), color=NM_YELLOW
        )
        greedy_label = Text("greedy 0.702", font_size=22, color=NM_YELLOW)
        greedy_label.next_to(greedy_line, DOWN, buff=0.1).align_to(greedy_line, RIGHT)
        self.play(Create(axes), FadeIn(x_labels), FadeIn(y_labels), run_time=0.8)
        self.play(Create(greedy_line), FadeIn(greedy_label), run_time=0.6)
        curve = VMobject(color=NM_GREEN).set_points_as_corners(points)
        dots = VGroup(*[Dot(p, color=NM_GREEN, radius=0.08) for p in points])
        values = VGroup(
            *[
                Text(f"{acc:.3f}", font_size=22, color=NM_GREEN).next_to(dot, UP, buff=0.12)
                for dot, (_, acc) in zip(dots, VOTE_BY_K)
            ]
        )
        self.play(Create(curve), FadeIn(dots), run_time=1.4)
        self.play(FadeIn(values), run_time=0.6)
        cost = Text(
            "k = 1 is one sample; each sample costs a full decode; flat after k ≈ 20",
            font_size=22,
            color=MUTED,
        )
        cost.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(cost), run_time=0.6)
        self.wait(2.4)
        self.clear_all()

    def show_limits(self) -> None:
        """What the toy does not show, in two readable screens."""
        header = Text("Limits", font_size=36, color=NM_PRIMARY)
        header.to_edge(UP, buff=0.4)
        first = bullet_list(
            (
                "Route diversity is built into the training data\n(3 fixed orders), not sampled freely",
                "Part of +0.104 only undoes greedy's poor route\nchoice: +0.068 over the best route",
                "Trace arm had extra budget: 150 vs 90 epochs,\n5.8x the supervised tokens",
            ),
            font_size=26,
        ).move_to(DOWN * 0.3)
        self.play(FadeIn(header), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(item) for item in first], lag_ratio=0.4), run_time=2.0)
        self.wait(3.2)
        self.play(FadeOut(first), run_time=0.5)
        second = bullet_list(
            (
                "Partial faithfulness: later steps follow a\ncorrupted first step only ~30-34% of the time",
                "Supervised scratchpads (Nye et al.), not\nWei et al.'s prompting of a ~100B model",
                f"Toy: {N_PARAMS}-parameter MLP, one seed,\ntest slice skewed to repeated digits",
            ),
            font_size=26,
        ).move_to(DOWN * 0.3)
        self.play(LaggedStart(*[FadeIn(item) for item in second], lag_ratio=0.4), run_time=2.0)
        self.wait(3.2)
        self.play(FadeOut(second), FadeOut(header), run_time=0.6)
