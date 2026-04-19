"""
Scene: TurboQuant
Script: microturboquant.py
Description: Random rotation makes per-coord scale uniform — absmax stops wasting bits
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from base import NM_BLUE, NM_GREEN, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


def _sample_rotation(dim: int, seed: int) -> np.ndarray:
    """Deterministic Haar-random rotation via Gram-Schmidt on Gaussian columns."""
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal((dim, dim))
    q, _ = np.linalg.qr(raw)
    return q


class TurboQuantScene(NoMagicScene):
    title_text = "TurboQuant"
    subtitle_text = "Rotate first — then every coordinate gets the same bit budget"

    def animate(self):
        # === Setup: anisotropic unit vector x in R^8 ===
        # One dominant coord, seven small coords — the regime where absmax wastes bits.
        x_raw = np.array([2.4, 0.30, -0.22, 0.15, -0.18, 0.25, -0.12, 0.20])
        x = x_raw / np.linalg.norm(x_raw)
        R = _sample_rotation(8, seed=42)
        y = R @ x  # Rotated coordinates — concentrated, uniform-ish scale.

        dim = len(x)
        bits = 4
        levels = 2 ** (bits - 1) - 1   # 7 levels per side for 4-bit absmax.

        # === Step 1: Show anisotropic x as a bar chart ===
        left_title = Text("x  (anisotropic input)", font_size=22, color=NM_BLUE, weight=BOLD)
        left_title.move_to(LEFT * 3.5 + UP * 3.0)

        bars_x = self._make_bars(x, center=LEFT * 3.5 + UP * 0.3, color=NM_BLUE)
        axis_x = self._make_axis(center=LEFT * 3.5 + DOWN * 0.5, label="coord")

        self.play(Write(left_title), Create(axis_x), run_time=0.6)
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars_x], lag_ratio=0.05),
            run_time=0.8,
        )
        self.wait(0.4)

        # === Step 2: Overlay absmax grid, highlight wasted bits ===
        # Baseline scale = max(|x|) / levels. Tiny coords collapse onto level 0.
        scale_base = float(np.max(np.abs(x))) / levels
        grid_x = self._make_quant_grid(
            center=LEFT * 3.5 + UP * 0.3, scale=scale_base, levels=levels, color=NM_YELLOW
        )
        caption_x = Text(
            "Small coords collapse to level 0 — bits wasted",
            font_size=16, color=NM_PRIMARY,
        )
        caption_x.move_to(LEFT * 3.5 + DOWN * 1.5)

        self.play(Create(grid_x), run_time=0.8)
        self.play(FadeIn(caption_x, shift=UP * 0.15), run_time=0.5)

        # Flash the small coords that round to 0 to drive the point home.
        small_bars = VGroup(*[bars_x[i] for i in range(dim) if abs(x[i]) < scale_base / 2])
        if len(small_bars) > 0:
            self.play(Indicate(small_bars, color=NM_PRIMARY, scale_factor=1.3), run_time=0.8)
        self.wait(0.6)

        # === Step 3: Apply rotation — visual arrow from left to right ===
        rotate_label = MathTex(r"y = R\,x", color=NM_ORANGE, font_size=40)
        rotate_label.move_to(UP * 0.3)
        arrow = Arrow(
            LEFT * 1.2 + UP * 0.3, RIGHT * 1.2 + UP * 0.3,
            color=NM_ORANGE, buff=0.1, stroke_width=4,
        )
        self.play(GrowArrow(arrow), Write(rotate_label), run_time=0.7)
        self.wait(0.4)

        # === Step 4: Show rotated y as bar chart on the right ===
        right_title = Text("y = R x  (rotated)", font_size=22, color=NM_GREEN, weight=BOLD)
        right_title.move_to(RIGHT * 3.5 + UP * 3.0)

        bars_y = self._make_bars(y, center=RIGHT * 3.5 + UP * 0.3, color=NM_GREEN)
        axis_y = self._make_axis(center=RIGHT * 3.5 + DOWN * 0.5, label="coord")

        self.play(Write(right_title), Create(axis_y), run_time=0.6)
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars_y], lag_ratio=0.05),
            run_time=0.8,
        )
        self.wait(0.4)

        # === Step 5: Overlay TurboQuant grid — every coord uses the full range ===
        scale_turbo = float(np.max(np.abs(y))) / levels
        grid_y = self._make_quant_grid(
            center=RIGHT * 3.5 + UP * 0.3, scale=scale_turbo, levels=levels, color=NM_YELLOW
        )
        caption_y = Text(
            "Every coord spans many levels — full budget used",
            font_size=16, color=NM_GREEN,
        )
        caption_y.move_to(RIGHT * 3.5 + DOWN * 1.5)

        self.play(Create(grid_y), run_time=0.8)
        self.play(FadeIn(caption_y, shift=UP * 0.15), run_time=0.5)
        self.wait(0.8)

        # === Step 6: IP-MSE comparison ===
        # Numbers taken from the script's observed output at 4 bits on D=32 synthetic data.
        comparison = VGroup(
            Text("absmax IP-MSE", font_size=18, color=NM_BLUE),
            Text("9e-4", font_size=18, color=NM_BLUE, weight=BOLD),
            Text("   vs   ", font_size=18, color=NM_TEXT),
            Text("TurboQuant IP-MSE", font_size=18, color=NM_GREEN),
            Text("5e-4", font_size=18, color=NM_GREEN, weight=BOLD),
            Text("  (1.6x better)", font_size=18, color=NM_YELLOW, weight=BOLD),
        ).arrange(RIGHT, buff=0.25)
        comparison.move_to(DOWN * 2.8)

        self.play(
            LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in comparison], lag_ratio=0.1),
            run_time=1.0,
        )
        self.wait(2.0)

        # Cleanup
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)

    # === Helpers ===

    def _make_bars(self, values, center, color) -> VGroup:
        """Build a row of vertical bars whose heights encode `values`."""
        bar_width = 0.22
        spacing = 0.32
        # Scale bar heights so the max bar is ~1.4 units tall.
        scale = 1.4 / max(abs(v) for v in values)
        bars = VGroup()
        n = len(values)
        total_span = (n - 1) * spacing
        for i, v in enumerate(values):
            height = abs(v) * scale
            bar = Rectangle(
                width=bar_width, height=max(height, 0.02),
                fill_color=color, fill_opacity=0.85, stroke_color=color, stroke_width=1.5,
            )
            x_offset = (i * spacing) - total_span / 2
            # Negative values point downward.
            direction = UP if v >= 0 else DOWN
            bar.move_to(center + RIGHT * x_offset + direction * (height / 2))
            bars.add(bar)
        return bars

    def _make_axis(self, center, label: str) -> VGroup:
        """Horizontal zero-line with a small label."""
        line = Line(LEFT * 1.3, RIGHT * 1.3, color=NM_TEXT, stroke_width=1.2)
        line.move_to(center)
        tag = Text(label, font_size=14, color=NM_TEXT)
        tag.next_to(line, RIGHT, buff=0.15)
        return VGroup(line, tag)

    def _make_quant_grid(self, center, scale: float, levels: int, color) -> VGroup:
        """Horizontal dashed lines at ±k*scale for k in 1..levels, near the bars.

        Each line marks a quantization boundary; bars falling between adjacent
        lines round to the same integer level. Lines above the bar region and
        below it make the available bit budget visible at a glance.
        """
        # Height normalization: same as _make_bars so grid aligns with bars.
        peak_values_proxy = levels * scale   # equals max(|values|) by construction
        height_scale = 1.4 / peak_values_proxy
        grid = VGroup()
        for k in range(1, levels + 1):
            for sign in (+1, -1):
                y = sign * k * scale * height_scale
                line = DashedLine(
                    LEFT * 1.4, RIGHT * 1.4,
                    color=color, stroke_width=0.8, stroke_opacity=0.5,
                    dash_length=0.08,
                )
                line.move_to(center + UP * y)
                grid.add(line)
        return grid
