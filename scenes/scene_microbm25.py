"""
Scene: BM25 Text Retrieval
Script: microbm25.py
Description: From TF-IDF to saturating term frequency — the BM25 scoring function
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_GRID, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


class BM25Scene(NoMagicScene):
    title_text = "BM25 Text Retrieval"
    subtitle_text = "From TF-IDF to saturating term frequency"

    def animate(self):
        # === Step 1: Show TF curve (unbounded, linear) ===
        axes = Axes(
            x_range=[0, 10, 2],
            y_range=[0, 10, 2],
            x_length=5,
            y_length=3.5,
            axis_config={"color": NM_GRID, "stroke_width": 1.5, "include_numbers": True,
                         "font_size": 14, "decimal_number_config": {"color": NM_TEXT}},
        )
        axes.move_to(LEFT * 2.5 + UP * 0.8)

        x_label = Text("term frequency (tf)", font_size=12, color=NM_TEXT)
        x_label.next_to(axes.x_axis, DOWN, buff=0.3)
        y_label = Text("score", font_size=12, color=NM_TEXT)
        y_label.next_to(axes.y_axis, LEFT, buff=0.2).shift(UP * 0.5)

        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), run_time=0.8)

        # TF-IDF: score = tf (linear, unbounded)
        tf_curve = axes.plot(lambda x: x, x_range=[0, 9.5], color=NM_ORANGE, stroke_width=2)
        tf_label = Text("TF-IDF: score = tf", font_size=14, color=NM_ORANGE, weight=BOLD)
        tf_label.next_to(axes, UP, buff=0.3).align_to(axes, LEFT)

        self.play(Create(tf_curve), Write(tf_label), run_time=0.8)
        self.wait(0.4)

        unbounded_note = Text("unbounded \u2014 keyword stuffing exploitable", font_size=11, color=NM_PRIMARY)
        unbounded_note.next_to(tf_label, DOWN, buff=0.1).align_to(tf_label, LEFT)
        self.play(FadeIn(unbounded_note), run_time=0.4)
        self.wait(0.4)

        # === Step 2: BM25 saturating curve ===
        k1 = 1.5
        def bm25_func(x):
            return (x * (k1 + 1)) / (x + k1)

        bm25_curve = axes.plot(bm25_func, x_range=[0, 9.5], color=NM_GREEN, stroke_width=2.5)
        bm25_label = Text("BM25: tf\u00b7(k1+1) / (tf + k1)", font_size=14, color=NM_GREEN, weight=BOLD)
        bm25_label.next_to(unbounded_note, DOWN, buff=0.15).align_to(tf_label, LEFT)

        self.play(Create(bm25_curve), Write(bm25_label), run_time=0.8)

        # Show asymptote line at k1+1
        asymptote = DashedLine(
            axes.c2p(0, k1 + 1), axes.c2p(9.5, k1 + 1),
            color=NM_YELLOW, stroke_width=1.5, dash_length=0.08,
        )
        asym_label = Text(f"k1+1 = {k1+1:.1f}", font_size=11, color=NM_YELLOW)
        asym_label.next_to(asymptote, RIGHT, buff=0.1)

        self.play(Create(asymptote), FadeIn(asym_label), run_time=0.5)

        sat_note = Text("saturates \u2014 diminishing returns from repetition", font_size=11, color=NM_GREEN)
        sat_note.next_to(bm25_label, DOWN, buff=0.1).align_to(tf_label, LEFT)
        self.play(FadeIn(sat_note), run_time=0.4)
        self.wait(0.6)

        # === Step 3: Document length normalization ===
        norm_panel = VGroup()
        norm_title = Text("Length Normalization (b parameter)", font_size=16, color=NM_BLUE, weight=BOLD)
        norm_title.move_to(RIGHT * 3.0 + UP * 2.5)

        b_vals = [
            ("b = 0.0", "no normalization", NM_ORANGE),
            ("b = 0.75", "standard (default)", NM_GREEN),
            ("b = 1.0", "full normalization", NM_BLUE),
        ]

        b_items = VGroup()
        for bv, desc, color in b_vals:
            line = VGroup(
                Text(bv, font_size=13, color=color, weight=BOLD),
                Text(f" \u2014 {desc}", font_size=12, color=NM_TEXT),
            ).arrange(RIGHT, buff=0.1)
            b_items.add(line)
        b_items.arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        b_items.next_to(norm_title, DOWN, buff=0.25)

        formula = Text("norm = 1 - b + b \u00b7 (dl / avgdl)", font_size=13, color=NM_YELLOW)
        formula.next_to(b_items, DOWN, buff=0.25)

        self.play(Write(norm_title), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(b, shift=UP * 0.1) for b in b_items], lag_ratio=0.12),
            run_time=0.6,
        )
        self.play(FadeIn(formula), run_time=0.4)
        self.wait(0.6)

        # === Step 4: Query scoring animation ===
        score_title = Text("Scoring a query against documents", font_size=16, color=NM_YELLOW, weight=BOLD)
        score_title.move_to(RIGHT * 3.0 + DOWN * 1.0)

        docs = VGroup()
        doc_data = [
            ("Doc A", "3 matches", 0.85, NM_GREEN),
            ("Doc B", "1 match", 0.35, NM_GRID),
            ("Doc C", "2 matches", 0.65, NM_BLUE),
        ]
        for name, desc, score, color in doc_data:
            bar_width = score * 2.5
            bar = Rectangle(
                width=bar_width, height=0.3,
                color=color, fill_opacity=0.5, stroke_width=1,
            )
            bar.align_to(RIGHT * 1.5, LEFT)
            name_t = Text(name, font_size=12, color=NM_TEXT)
            name_t.next_to(bar, LEFT, buff=0.15)
            score_t = Text(f"{score:.2f}", font_size=11, color=NM_YELLOW)
            score_t.next_to(bar, RIGHT, buff=0.1)
            docs.add(VGroup(bar, name_t, score_t))

        docs.arrange(DOWN, buff=0.12)
        docs.next_to(score_title, DOWN, buff=0.25)

        self.play(Write(score_title), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(d, shift=RIGHT * 0.2) for d in docs], lag_ratio=0.12),
            run_time=0.8,
        )

        # Highlight top doc
        top_rect = SurroundingRectangle(docs[0], color=NM_GREEN, buff=0.05, stroke_width=1.5)
        self.play(Create(top_rect), run_time=0.4)
        self.wait(1.6)

        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
