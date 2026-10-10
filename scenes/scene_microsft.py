"""
Scene: Supervised Fine-Tuning (SFT)
Script: microsft.py
Description: Pretrain a tiny decoder, then train the same weights on response-masked demonstrations
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_GRID, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


def make_token(text: str, color: str, fill_opacity: float = 0.25, width: float = 0.62) -> VGroup:
    """A rounded token box with its character centered inside."""
    box = RoundedRectangle(
        corner_radius=0.08,
        width=width,
        height=0.55,
        color=color,
        fill_opacity=fill_opacity,
        stroke_width=1.5,
    )
    label = Text(text, font_size=20, color=NM_TEXT)
    label.move_to(box.get_center())
    return VGroup(box, label)


def make_row(tokens: list[str], colors: list[str], width: float = 0.62) -> VGroup:
    """A horizontal row of token boxes."""
    return VGroup(*[make_token(t, c, width=width) for t, c in zip(tokens, colors)]).arrange(
        RIGHT, buff=0.08
    )


class SFTScene(NoMagicScene):
    title_text = "Supervised Fine-Tuning"
    subtitle_text = "Same pretrained weights, synthetic toy pairs, answer-only loss"

    def animate(self) -> None:
        self.show_pretraining()
        self.show_masked_loss()
        self.show_update_and_inference()

    def show_pretraining(self) -> None:
        """Stage 1: next-token pretraining on plain cyclic strings."""
        header = Text("Stage 1 — pretrain on plain text", font_size=26, color=NM_TEXT, weight=BOLD)
        header.to_edge(UP, buff=0.5)
        tokens = ["⟨B⟩", "a", "b", "c", "d", "e", "f", "g", "h", "⟨B⟩"]
        row = make_row(tokens, [NM_GRID] + [NM_BLUE] * 8 + [NM_GRID])
        row.move_to(UP * 0.6)
        idx = VGroup(
            *[
                Text(str(i), font_size=14, color=NM_TEXT).next_to(row[i], DOWN, buff=0.12)
                for i in range(len(tokens))
            ]
        )
        self.play(FadeIn(header), LaggedStart(*[FadeIn(t) for t in row], lag_ratio=0.06))
        self.play(FadeIn(idx), run_time=0.5)

        # Every next token is a target: position t-1 predicts token t (9 targets).
        arrows = VGroup(
            *[
                CurvedArrow(
                    row[i].get_top() + UP * 0.05,
                    row[i + 1].get_top() + UP * 0.05,
                    angle=-TAU / 4,
                    color=NM_GREEN,
                    stroke_width=2,
                    tip_length=0.12,
                )
                for i in range(len(tokens) - 1)
            ]
        )
        note = Text(
            "loss on all 9 next tokens · 200 updates, one sampled string each",
            font_size=18,
            color=NM_GREEN,
        )
        note.next_to(idx, DOWN, buff=0.5)
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.08), run_time=1.6)
        self.play(FadeIn(note), run_time=0.6)

        unseen = Text(
            "n o p t x y : >  never appear here → their embeddings stay at initialization",
            font_size=16,
            color=NM_YELLOW,
        )
        unseen.next_to(note, DOWN, buff=0.35)
        self.play(FadeIn(unseen), run_time=0.6)
        self.wait(1.6)

        snapshot = Text(
            "keep the learned weights θ_base  (no reinitialization)",
            font_size=22,
            color=NM_TEXT,
        )
        snapshot.move_to(DOWN * 2.9)
        self.play(FadeIn(snapshot, shift=UP * 0.2), run_time=0.7)
        self.wait(1.2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)

    def show_masked_loss(self) -> None:
        """Stage 2: a demonstration, its response-only targets and the batch mean."""
        header = Text(
            "Stage 2 — fine-tune the same weights", font_size=26, color=NM_TEXT, weight=BOLD
        )
        header.to_edge(UP, buff=0.5)
        tokens = ["⟨B⟩", "c", "o", "p", "y", ":", "a", ">", "a", "⟨B⟩"]
        colors = [NM_GRID] * 8 + [NM_PRIMARY, NM_PRIMARY]
        row = make_row(tokens, colors)
        row.move_to(UP * 0.7)
        idx = VGroup(
            *[
                Text(str(i), font_size=14, color=NM_TEXT).next_to(row[i], DOWN, buff=0.12)
                for i in range(len(tokens))
            ]
        )
        prompt_brace = Brace(VGroup(*row[:8]), UP, color=NM_TEXT)
        prompt_label = Text("prompt: input only, no target", font_size=16, color=NM_TEXT)
        prompt_label.next_to(prompt_brace, UP, buff=0.08)
        resp_brace = Brace(VGroup(*row[8:]), UP, color=NM_PRIMARY)
        resp_label = Text("targets", font_size=16, color=NM_PRIMARY)
        resp_label.next_to(resp_brace, UP, buff=0.08)
        self.play(FadeIn(header), LaggedStart(*[FadeIn(t) for t in row], lag_ratio=0.05))
        self.play(
            FadeIn(idx),
            GrowFromCenter(prompt_brace),
            FadeIn(prompt_label),
            GrowFromCenter(resp_brace),
            FadeIn(resp_label),
            run_time=0.9,
        )

        # Causal shift: positions 7 and 8 predict tokens 8 and 9.
        shift_arrows = VGroup(
            *[
                CurvedArrow(
                    row[i].get_bottom() + DOWN * 0.35,
                    row[i + 1].get_bottom() + DOWN * 0.35,
                    angle=TAU / 4,
                    color=NM_PRIMARY,
                    stroke_width=2.5,
                    tip_length=0.14,
                )
                for i in (7, 8)
            ]
        )
        pair_loss = Text(
            "L_pair = −½ [ log p(x₈ | x₀..x₇) + log p(x₉ | x₀..x₈) ]",
            font_size=22,
            color=NM_TEXT,
        )
        pair_loss.move_to(DOWN * 1.0)
        self.play(LaggedStart(*[Create(a) for a in shift_arrows], lag_ratio=0.3), run_time=1.0)
        self.play(Write(pair_loss), run_time=1.4)

        # Masking removes prompt targets, not prompt inputs: attention reads them.
        attn = CurvedArrow(
            row[7].get_top() + UP * 1.3,
            row[2].get_top() + UP * 1.3,
            angle=TAU / 6,
            color=NM_YELLOW,
            stroke_width=2,
            tip_length=0.12,
        )
        attn_note = Text(
            "gradient still reaches the prompt through attention", font_size=16, color=NM_YELLOW
        )
        attn_note.next_to(pair_loss, DOWN, buff=0.35)
        self.play(Create(attn), FadeIn(attn_note), run_time=1.0)

        batch = Text(
            "L = (1/14) Σ L_pair  over all 14 training pairs  (mean of 28 targets)",
            font_size=20,
            color=NM_GREEN,
        )
        batch.next_to(attn_note, DOWN, buff=0.4)
        held = Text(
            "copy:h> and next:h> are held out — reported, never trained or tuned on",
            font_size=16,
            color=NM_TEXT,
        )
        held.next_to(batch, DOWN, buff=0.3)
        self.play(FadeIn(batch, shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(held), run_time=0.6)
        self.wait(2.2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)

    def show_update_and_inference(self) -> None:
        """Parameter update, then greedy decoding from the trained logits."""
        update = VGroup(
            Text("θ ← Adam step on ∇θ L", font_size=26, color=NM_TEXT),
            Text(
                "300 updates · Adam moments restart at the stage boundary",
                font_size=18,
                color=NM_GREEN,
            ),
            Text(
                "every weight can change: full-parameter fine-tuning", font_size=18, color=NM_TEXT
            ),
        ).arrange(DOWN, buff=0.25)
        update.move_to(UP * 1.9)
        self.play(FadeIn(update[0], shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(update[1]), FadeIn(update[2]), run_time=0.8)

        prompt = make_row(["⟨B⟩", "n", "e", "x", "t", ":", "c", ">"], [NM_GRID] * 8)
        prompt.move_to(LEFT * 2.2 + DOWN * 0.6)
        model = RoundedRectangle(
            corner_radius=0.15, width=2.2, height=1.0, color=NM_BLUE, fill_opacity=0.2
        )
        model.next_to(prompt, RIGHT, buff=0.5)
        model_label = Text("fine-tuned\ndecoder", font_size=16, color=NM_TEXT)
        model_label.move_to(model.get_center())
        out = make_token("?", NM_PRIMARY, fill_opacity=0.35)
        out.next_to(model, RIGHT, buff=0.6)
        a1 = Arrow(prompt.get_right(), model.get_left(), buff=0.08, color=NM_TEXT, stroke_width=2)
        a2 = Arrow(model.get_right(), out.get_left(), buff=0.08, color=NM_TEXT, stroke_width=2)
        rule = Text(
            "next token = argmax softmax(logits / 1), repeated until ⟨end⟩",
            font_size=18,
            color=NM_TEXT,
        )
        rule.move_to(DOWN * 2.0)
        caveat = Text(
            "answers come from the trained logits — no lookup of the demonstration rule",
            font_size=16,
            color=NM_YELLOW,
        )
        caveat.next_to(rule, DOWN, buff=0.3)
        self.play(FadeIn(prompt), FadeIn(model), FadeIn(model_label), Create(a1), run_time=1.0)
        self.play(Create(a2), FadeIn(out), run_time=0.7)
        self.play(FadeIn(rule), run_time=0.6)
        self.play(FadeIn(caveat), run_time=0.6)
        self.wait(2.2)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
