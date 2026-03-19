"""
Scene: Vision Transformer
Script: microvit.py
Description: An image is worth 16x16 words — patches to transformer to classification
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


class ViTScene(NoMagicScene):
    title_text = "Vision Transformer"
    subtitle_text = "An image is worth 16\u00d716 words"

    def animate(self):
        # === Step 1: Show an image as a grid of pixels ===
        img_label = Text("Input Image", font_size=18, color=NM_BLUE, weight=BOLD)
        img_label.move_to(LEFT * 4.5 + UP * 2.8)

        grid_size = 4
        cell_size = 0.5
        img_cells = VGroup()
        patch_colors = [
            [NM_BLUE, NM_BLUE, NM_GREEN, NM_GREEN],
            [NM_BLUE, NM_BLUE, NM_GREEN, NM_GREEN],
            [NM_ORANGE, NM_ORANGE, NM_PURPLE, NM_PURPLE],
            [NM_ORANGE, NM_ORANGE, NM_PURPLE, NM_PURPLE],
        ]
        for r in range(grid_size):
            for c in range(grid_size):
                sq = Square(
                    side_length=cell_size, stroke_width=0.5, stroke_color=NM_GRID,
                )
                sq.set_fill(patch_colors[r][c], opacity=0.4)
                sq.move_to(
                    LEFT * 4.5
                    + RIGHT * (c - grid_size / 2 + 0.5) * cell_size
                    + DOWN * (r - grid_size / 2 + 0.5) * cell_size
                    + UP * 0.8
                )
                img_cells.add(sq)

        self.play(Write(img_label), FadeIn(img_cells), run_time=0.8)
        self.wait(0.4)

        # === Step 2: Split into 2x2 patches ===
        patch_label = Text("Split into patches", font_size=14, color=NM_YELLOW)
        patch_label.next_to(img_cells, DOWN, buff=0.3)
        self.play(FadeIn(patch_label), run_time=0.3)

        # Highlight patch boundaries
        for i in range(0, grid_size, 2):
            for j in range(0, grid_size, 2):
                top_left = img_cells[i * grid_size + j]
                bot_right = img_cells[(i + 1) * grid_size + (j + 1)]
                rect = SurroundingRectangle(
                    VGroup(top_left, bot_right),
                    color=NM_YELLOW, stroke_width=2, buff=0.02,
                )
                self.play(Create(rect), run_time=0.3)
        self.wait(0.4)

        # === Step 3: Flatten patches into a sequence ===
        seq_label = Text("Patch Sequence", font_size=18, color=NM_YELLOW, weight=BOLD)
        seq_label.move_to(UP * 2.8)

        patch_names = ["P1", "P2", "P3", "P4"]
        patch_seq_colors = [NM_BLUE, NM_GREEN, NM_ORANGE, NM_PURPLE]
        token_boxes = VGroup()

        # CLS token first
        cls_box = RoundedRectangle(
            corner_radius=0.08, width=0.8, height=0.5,
            color=NM_PRIMARY, fill_opacity=0.3, stroke_width=1.5,
        )
        cls_text = Text("[CLS]", font_size=12, color=NM_PRIMARY, weight=BOLD)
        cls_text.move_to(cls_box.get_center())
        token_boxes.add(VGroup(cls_box, cls_text))

        for name, color in zip(patch_names, patch_seq_colors):
            box = RoundedRectangle(
                corner_radius=0.08, width=0.8, height=0.5,
                color=color, fill_opacity=0.25, stroke_width=1.5,
            )
            text = Text(name, font_size=13, color=color)
            text.move_to(box.get_center())
            token_boxes.add(VGroup(box, text))

        token_boxes.arrange(RIGHT, buff=0.15)
        token_boxes.move_to(UP * 1.5)

        self.play(Write(seq_label), run_time=0.3)
        self.play(
            LaggedStart(*[FadeIn(t, shift=UP * 0.15) for t in token_boxes], lag_ratio=0.1),
            run_time=0.9,
        )

        # === Step 4: Add position embeddings ===
        pos_label = Text("+ Position Embeddings", font_size=14, color=NM_GREEN)
        pos_label.next_to(token_boxes, DOWN, buff=0.2)

        pos_arrows = VGroup()
        for tb in token_boxes:
            arr = Arrow(
                tb.get_bottom() + DOWN * 0.15, tb.get_bottom(),
                color=NM_GREEN, stroke_width=1, buff=0, tip_length=0.08,
            )
            pos_arrows.add(arr)

        self.play(FadeIn(pos_label), run_time=0.3)
        self.play(
            LaggedStart(*[GrowArrow(a) for a in pos_arrows], lag_ratio=0.06),
            run_time=0.5,
        )
        self.wait(0.4)

        # === Step 5: Transformer encoder block ===
        encoder_box = RoundedRectangle(
            corner_radius=0.12, width=5.5, height=1.2,
            color=NM_BLUE, fill_opacity=0.1, stroke_width=2,
        )
        encoder_box.move_to(DOWN * 0.5)

        enc_parts = VGroup(
            Text("Self-Attention", font_size=14, color=NM_BLUE),
            Text("\u2192", font_size=18, color=NM_GRID),
            Text("LayerNorm", font_size=14, color=NM_TEXT),
            Text("\u2192", font_size=18, color=NM_GRID),
            Text("MLP", font_size=14, color=NM_PURPLE),
            Text("\u2192", font_size=18, color=NM_GRID),
            Text("LayerNorm", font_size=14, color=NM_TEXT),
        ).arrange(RIGHT, buff=0.15)
        enc_parts.move_to(encoder_box.get_center())

        enc_label = Text("Transformer Encoder (\u00d7N)", font_size=16, color=NM_BLUE, weight=BOLD)
        enc_label.next_to(encoder_box, UP, buff=0.15)

        # Arrows from sequence to encoder
        seq_to_enc = Arrow(
            token_boxes.get_bottom() + DOWN * 0.3, encoder_box.get_top(),
            color=NM_GRID, stroke_width=1.5, buff=0.05, tip_length=0.1,
        )

        self.play(
            GrowArrow(seq_to_enc),
            FadeIn(encoder_box), FadeIn(enc_parts), Write(enc_label),
            run_time=0.8,
        )
        self.wait(0.4)

        # === Step 6: Classification head from [CLS] token ===
        cls_output = RoundedRectangle(
            corner_radius=0.08, width=1.0, height=0.5,
            color=NM_PRIMARY, fill_opacity=0.3, stroke_width=1.5,
        )
        cls_out_text = Text("[CLS]", font_size=12, color=NM_PRIMARY, weight=BOLD)
        cls_out_text.move_to(cls_output.get_center())
        cls_output_group = VGroup(cls_output, cls_out_text)
        cls_output_group.move_to(DOWN * 2.0 + LEFT * 2.0)

        cls_arrow = Arrow(
            encoder_box.get_bottom() + LEFT * 2.0, cls_output_group.get_top(),
            color=NM_PRIMARY, stroke_width=1.5, buff=0.05, tip_length=0.1,
        )

        class_head = RoundedRectangle(
            corner_radius=0.08, width=1.5, height=0.5,
            color=NM_GREEN, fill_opacity=0.2, stroke_width=1.5,
        )
        class_text = Text("MLP Head", font_size=13, color=NM_GREEN)
        class_text.move_to(class_head.get_center())
        class_group = VGroup(class_head, class_text)
        class_group.move_to(DOWN * 2.0 + RIGHT * 0.5)

        head_arrow = Arrow(
            cls_output_group.get_right(), class_group.get_left(),
            color=NM_GREEN, stroke_width=1.5, buff=0.05, tip_length=0.1,
        )

        pred_text = Text("\"cat\"", font_size=18, color=NM_GREEN, weight=BOLD)
        pred_text.next_to(class_group, RIGHT, buff=0.3)

        self.play(GrowArrow(cls_arrow), FadeIn(cls_output_group), run_time=0.5)
        self.play(GrowArrow(head_arrow), FadeIn(class_group), run_time=0.5)
        self.play(FadeIn(pred_text, scale=1.2), run_time=0.5)

        # === Step 7: Summary ===
        summary = Text(
            "No convolutions — pure attention on image patches",
            font_size=14, color=NM_YELLOW, weight=BOLD,
        )
        summary.move_to(DOWN * 3.2)
        self.play(FadeIn(summary), run_time=0.5)
        self.wait(1.6)

        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
