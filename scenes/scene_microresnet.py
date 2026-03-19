"""
Scene: Residual Networks
Script: microresnet.py
Description: Skip connections as gradient highways — F(x) + x keeps gradients alive
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_GREEN, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


def make_layer_box(label, color, width=1.0, height=0.5):
    """Create a network layer box."""
    box = RoundedRectangle(
        corner_radius=0.08, width=width, height=height,
        color=color, fill_opacity=0.2, stroke_width=1.5,
    )
    text = Text(label, font_size=13, color=color)
    text.move_to(box.get_center())
    return VGroup(box, text)


class ResNetScene(NoMagicScene):
    title_text = "Residual Networks"
    subtitle_text = "Skip connections as gradient highways"

    def animate(self):
        n_layers = 6

        # === Step 1: Plain deep network (no skips) ===
        plain_label = Text("Plain Network", font_size=20, color=NM_PRIMARY, weight=BOLD)
        plain_label.move_to(LEFT * 3.5 + UP * 3.0)
        self.play(Write(plain_label), run_time=0.4)

        plain_layers = VGroup()
        for i in range(n_layers):
            layer = make_layer_box(f"L{i+1}", NM_PRIMARY)
            plain_layers.add(layer)
        plain_layers.arrange(DOWN, buff=0.25)
        plain_layers.move_to(LEFT * 3.5 + DOWN * 0.2)

        plain_arrows = VGroup()
        for i in range(n_layers - 1):
            arr = Arrow(
                plain_layers[i].get_bottom(), plain_layers[i + 1].get_top(),
                color=NM_PRIMARY, stroke_width=1.5, buff=0.05, tip_length=0.1,
            )
            plain_arrows.add(arr)

        self.play(
            LaggedStart(*[FadeIn(l) for l in plain_layers], lag_ratio=0.08),
            LaggedStart(*[GrowArrow(a) for a in plain_arrows], lag_ratio=0.08),
            run_time=0.9,
        )

        # === Step 2: Animate vanishing gradient in plain network ===
        grad_label = Text("Gradient flow", font_size=14, color=NM_YELLOW)
        grad_label.next_to(plain_layers[-1], LEFT, buff=0.4)
        self.play(FadeIn(grad_label), run_time=0.3)

        # Gradient arrows shrinking from bottom to top
        grad_arrows = VGroup()
        for i in range(n_layers):
            idx = n_layers - 1 - i
            strength = 0.9 * (0.5 ** i)
            arr = Arrow(
                plain_layers[idx].get_left() + LEFT * 0.3,
                plain_layers[idx].get_left() + LEFT * 0.3 + UP * 0.3,
                color=NM_YELLOW, stroke_width=max(0.5, 3 * strength),
                buff=0, tip_length=0.08, stroke_opacity=max(0.15, strength),
            )
            grad_arrows.add(arr)

        self.play(
            LaggedStart(*[GrowArrow(a) for a in grad_arrows], lag_ratio=0.1),
            run_time=1.0,
        )

        vanish_text = Text("gradients vanish", font_size=12, color=NM_PRIMARY)
        vanish_text.next_to(plain_layers[0], LEFT, buff=0.5)
        self.play(FadeIn(vanish_text), run_time=0.4)
        self.wait(0.6)

        # === Step 3: ResNet with skip connections ===
        res_label = Text("Residual Network", font_size=20, color=NM_GREEN, weight=BOLD)
        res_label.move_to(RIGHT * 3.0 + UP * 3.0)
        self.play(Write(res_label), run_time=0.4)

        res_layers = VGroup()
        for i in range(n_layers):
            layer = make_layer_box(f"L{i+1}", NM_GREEN)
            res_layers.add(layer)
        res_layers.arrange(DOWN, buff=0.25)
        res_layers.move_to(RIGHT * 3.0 + DOWN * 0.2)

        res_arrows = VGroup()
        for i in range(n_layers - 1):
            arr = Arrow(
                res_layers[i].get_bottom(), res_layers[i + 1].get_top(),
                color=NM_GREEN, stroke_width=1.5, buff=0.05, tip_length=0.1,
            )
            res_arrows.add(arr)

        self.play(
            LaggedStart(*[FadeIn(l) for l in res_layers], lag_ratio=0.08),
            LaggedStart(*[GrowArrow(a) for a in res_arrows], lag_ratio=0.08),
            run_time=0.9,
        )

        # Skip connections every 2 layers
        skip_arrows = VGroup()
        for i in range(0, n_layers - 2, 2):
            skip = CurvedArrow(
                res_layers[i].get_right() + RIGHT * 0.1,
                res_layers[i + 2].get_right() + RIGHT * 0.1,
                color=NM_YELLOW, stroke_width=2, angle=-TAU / 6,
            )
            plus = Text("+", font_size=16, color=NM_YELLOW, weight=BOLD)
            plus.next_to(res_layers[i + 2], RIGHT, buff=0.6)
            skip_arrows.add(VGroup(skip, plus))

        self.play(
            LaggedStart(*[Create(s[0]) for s in skip_arrows], lag_ratio=0.15),
            LaggedStart(*[FadeIn(s[1]) for s in skip_arrows], lag_ratio=0.15),
            run_time=0.9,
        )
        self.wait(0.4)

        # === Step 4: Gradient flows strongly through skip connections ===
        res_grad_arrows = VGroup()
        for i in range(n_layers):
            idx = n_layers - 1 - i
            strength = 0.9 * (0.85 ** i)  # Much slower decay
            arr = Arrow(
                res_layers[idx].get_left() + LEFT * 0.3,
                res_layers[idx].get_left() + LEFT * 0.3 + UP * 0.3,
                color=NM_YELLOW, stroke_width=max(0.5, 3 * strength),
                buff=0, tip_length=0.08, stroke_opacity=max(0.3, strength),
            )
            res_grad_arrows.add(arr)

        self.play(
            LaggedStart(*[GrowArrow(a) for a in res_grad_arrows], lag_ratio=0.1),
            run_time=1.0,
        )

        strong_text = Text("gradients preserved", font_size=12, color=NM_GREEN)
        strong_text.next_to(res_layers[0], LEFT, buff=0.5)
        self.play(FadeIn(strong_text), run_time=0.4)
        self.wait(0.6)

        # === Step 5: Residual block formula ===
        formula = VGroup(
            Text("Residual block:", font_size=16, color=NM_TEXT),
            Text("y = F(x) + x", font_size=20, color=NM_GREEN, weight=BOLD),
            Text("Network only learns the residual F(x)", font_size=13, color=NM_YELLOW),
        ).arrange(DOWN, buff=0.1)
        formula.move_to(DOWN * 3.0)

        self.play(
            LaggedStart(*[FadeIn(f, shift=UP * 0.1) for f in formula], lag_ratio=0.15),
            run_time=0.8,
        )
        self.wait(1.6)

        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
