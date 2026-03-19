"""
Scene: Speculative Decoding
Script: microspeculative.py
Description: Draft fast, verify once — small model drafts, large model checks in parallel
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


def make_token(text, color, fill_opacity=0.3):
    """Create a small token box."""
    box = RoundedRectangle(
        corner_radius=0.06, width=0.7, height=0.45,
        color=color, fill_opacity=fill_opacity, stroke_width=1.5,
    )
    label = Text(text, font_size=14, color=NM_TEXT)
    label.move_to(box.get_center())
    return VGroup(box, label)


class SpeculativeScene(NoMagicScene):
    title_text = "Speculative Decoding"
    subtitle_text = "Draft fast, verify once"

    def animate(self):
        # === Step 1: Show standard autoregressive (slow) ===
        std_label = Text("Standard: 1 token per forward pass", font_size=18, color=NM_PRIMARY, weight=BOLD)
        std_label.move_to(UP * 3.0)
        self.play(Write(std_label), run_time=0.4)

        # Show sequential generation
        std_tokens = VGroup()
        token_texts = ["The", "cat", "sat", "on", "the"]
        for i, t in enumerate(token_texts):
            tok = make_token(t, NM_PRIMARY, fill_opacity=0.25)
            std_tokens.add(tok)
        std_tokens.arrange(RIGHT, buff=0.15)
        std_tokens.move_to(UP * 2.0)

        for i, tok in enumerate(std_tokens):
            self.play(FadeIn(tok, scale=1.2), run_time=0.3)

        # Show "5 forward passes" counter
        std_count = Text("5 forward passes (slow)", font_size=13, color=NM_PRIMARY)
        std_count.next_to(std_tokens, RIGHT, buff=0.3)
        self.play(FadeIn(std_count), run_time=0.3)
        self.wait(0.4)

        # === Step 2: Speculative decoding — draft model ===
        draft_label = Text("Draft Model (small, fast)", font_size=18, color=NM_BLUE, weight=BOLD)
        draft_label.move_to(LEFT * 3.0 + UP * 0.5)

        draft_box = RoundedRectangle(
            corner_radius=0.1, width=1.5, height=0.8,
            color=NM_BLUE, fill_opacity=0.15, stroke_width=1.5,
        )
        draft_icon = Text("7B", font_size=16, color=NM_BLUE)
        draft_icon.move_to(draft_box.get_center())
        draft_model = VGroup(draft_box, draft_icon)
        draft_model.move_to(LEFT * 4.5 + DOWN * 0.5)

        self.play(Write(draft_label), FadeIn(draft_model), run_time=0.5)

        # Draft generates K=4 tokens quickly
        draft_tokens = VGroup()
        draft_texts = ["cat", "sat", "on", "the"]
        for t in draft_texts:
            tok = make_token(t, NM_BLUE, fill_opacity=0.2)
            draft_tokens.add(tok)
        draft_tokens.arrange(RIGHT, buff=0.1)
        draft_tokens.move_to(LEFT * 1.5 + DOWN * 0.5)

        draft_arrow = Arrow(
            draft_model.get_right(), draft_tokens.get_left(),
            color=NM_BLUE, stroke_width=1.5, buff=0.1, tip_length=0.1,
        )
        fast_text = Text("4 tokens, fast", font_size=11, color=NM_BLUE)
        fast_text.next_to(draft_arrow, UP, buff=0.05)

        self.play(GrowArrow(draft_arrow), FadeIn(fast_text), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(t, shift=RIGHT * 0.15) for t in draft_tokens], lag_ratio=0.08),
            run_time=0.6,
        )
        self.wait(0.4)

        # === Step 3: Verifier model checks in parallel ===
        verify_label = Text("Verifier Model (large, accurate)", font_size=18, color=NM_GREEN, weight=BOLD)
        verify_label.move_to(LEFT * 3.0 + DOWN * 1.8)

        verify_box = RoundedRectangle(
            corner_radius=0.1, width=1.5, height=0.8,
            color=NM_GREEN, fill_opacity=0.15, stroke_width=1.5,
        )
        verify_icon = Text("70B", font_size=16, color=NM_GREEN)
        verify_icon.move_to(verify_box.get_center())
        verify_model = VGroup(verify_box, verify_icon)
        verify_model.move_to(LEFT * 4.5 + DOWN * 2.8)

        self.play(Write(verify_label), FadeIn(verify_model), run_time=0.5)

        # Arrow from draft tokens to verifier
        verify_arrow = Arrow(
            draft_tokens.get_bottom(), verify_model.get_right() + UP * 0.2,
            color=NM_YELLOW, stroke_width=1.5, buff=0.1, tip_length=0.1,
        )
        parallel_text = Text("1 forward pass (parallel)", font_size=11, color=NM_YELLOW)
        parallel_text.next_to(verify_arrow, RIGHT, buff=0.1)

        self.play(GrowArrow(verify_arrow), FadeIn(parallel_text), run_time=0.5)
        self.wait(0.3)

        # === Step 4: Accept/Reject decisions ===
        decisions = VGroup()
        results = [
            ("cat", True), ("sat", True), ("on", True), ("the", True),
        ]
        for i, (tok_text, accepted) in enumerate(results):
            color = NM_GREEN if accepted else NM_PRIMARY
            symbol = "\u2713" if accepted else "\u2717"
            check = Text(symbol, font_size=18, color=color, weight=BOLD)
            check.next_to(draft_tokens[i], DOWN, buff=0.5)
            decisions.add(check)

        self.play(
            LaggedStart(*[FadeIn(d, scale=1.3) for d in decisions], lag_ratio=0.1),
            run_time=0.8,
        )
        self.wait(0.4)

        # Recolor accepted tokens green
        for i, (_, accepted) in enumerate(results):
            if accepted:
                self.play(
                    draft_tokens[i][0].animate.set_fill(NM_GREEN, opacity=0.3)
                        .set_stroke(NM_GREEN),
                    run_time=0.15,
                )
        self.wait(0.4)

        # === Step 5: Speedup summary ===
        summary = VGroup(
            Text("Standard: K tokens = K forward passes", font_size=14, color=NM_PRIMARY),
            Text("Speculative: K tokens = 1 draft + 1 verify", font_size=14, color=NM_GREEN, weight=BOLD),
            Text("2-3x speedup with no quality loss", font_size=16, color=NM_YELLOW, weight=BOLD),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        summary.move_to(RIGHT * 3.0 + DOWN * 2.5)

        self.play(
            LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in summary], lag_ratio=0.15),
            run_time=0.8,
        )
        self.wait(1.6)

        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
