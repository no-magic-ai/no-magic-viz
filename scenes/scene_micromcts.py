"""
Scene: Monte Carlo Tree Search
Script: micromcts.py
Description: UCB1-guided tree search — select, expand, simulate, backpropagate
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_GRID, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


def make_tree_node(label, color, radius=0.3, fill_opacity=0.25):
    """Create a circular tree node with a label."""
    circle = Circle(radius=radius, color=color, fill_opacity=fill_opacity, stroke_width=2)
    text = Text(label, font_size=14, color=NM_TEXT)
    return VGroup(circle, text)


class MCTSScene(NoMagicScene):
    title_text = "Monte Carlo Tree Search"
    subtitle_text = "UCB1-guided exploration of game trees"

    def animate(self):
        # === Step 1: Show the 4 MCTS phases ===
        phase_names = ["SELECT", "EXPAND", "SIMULATE", "BACKPROPAGATE"]
        phase_colors = [NM_BLUE, NM_GREEN, NM_ORANGE, NM_PRIMARY]
        phase_boxes = VGroup()

        for name, color in zip(phase_names, phase_colors):
            box = VGroup(
                RoundedRectangle(
                    corner_radius=0.1, width=2.2, height=0.6,
                    color=color, fill_opacity=0.2, stroke_width=1.5,
                ),
                Text(name, font_size=16, color=color, weight=BOLD),
            )
            phase_boxes.add(box)

        phase_boxes.arrange(RIGHT, buff=0.4)
        phase_boxes.to_edge(UP, buff=0.5)
        self.play(
            LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in phase_boxes], lag_ratio=0.15),
            run_time=1.2,
        )

        arrows_between = VGroup()
        for i in range(len(phase_boxes) - 1):
            arrow = Arrow(
                phase_boxes[i].get_right(), phase_boxes[i + 1].get_left(),
                buff=0.08, color=NM_GRID, stroke_width=2,
            )
            arrows_between.add(arrow)

        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows_between], lag_ratio=0.1),
            run_time=0.6,
        )
        self.wait(0.5)

        # === Step 2: Build a game tree ===
        root = make_tree_node("R", NM_PRIMARY, radius=0.3)
        root.move_to(UP * 0.3)

        children = VGroup()
        child_labels = ["A", "B", "C"]
        child_positions = [LEFT * 2.5 + DOWN * 1.2, DOWN * 1.2, RIGHT * 2.5 + DOWN * 1.2]

        for label, pos in zip(child_labels, child_positions):
            node = make_tree_node(label, NM_BLUE)
            node.move_to(pos)
            children.add(node)

        edges_l1 = VGroup()
        for child in children:
            edge = Line(root.get_bottom(), child.get_top(), color=NM_GRID, stroke_width=1.5)
            edges_l1.add(edge)

        self.play(FadeIn(root), run_time=0.5)
        self.play(
            LaggedStart(*[Create(e) for e in edges_l1], lag_ratio=0.1),
            LaggedStart(*[FadeIn(c, scale=0.8) for c in children], lag_ratio=0.1),
            run_time=0.9,
        )

        # Win/visit stats
        stats = ["2/5", "1/3", "3/7"]
        stat_labels = VGroup()
        for child, stat in zip(children, stats):
            sl = Text(stat, font_size=12, color=NM_YELLOW)
            sl.next_to(child, DOWN, buff=0.15)
            stat_labels.add(sl)

        self.play(
            LaggedStart(*[FadeIn(s) for s in stat_labels], lag_ratio=0.1),
            run_time=0.6,
        )
        self.wait(0.5)

        # === Step 3: SELECT — highlight UCB1 formula and best node ===
        self.play(Indicate(phase_boxes[0], color=NM_BLUE, scale_factor=1.08), run_time=0.5)

        ucb_formula = MathTex(
            r"\text{UCB1} = \frac{w_i}{n_i} + c \sqrt{\frac{\ln N}{n_i}}",
            font_size=28, color=NM_YELLOW,
        )
        ucb_formula.to_edge(DOWN, buff=0.8)
        self.play(Write(ucb_formula), run_time=1.0)
        self.wait(0.5)

        # Highlight node C as best UCB1
        self.play(
            children[2][0].animate.set_fill(NM_GREEN, opacity=0.5),
            children[2][0].animate.set_stroke(NM_GREEN),
            run_time=0.6,
        )
        select_arrow = Arrow(
            root.get_bottom(), children[2].get_top(),
            buff=0.1, color=NM_GREEN, stroke_width=3,
        )
        self.play(GrowArrow(select_arrow), run_time=0.5)
        self.wait(0.5)

        # === Step 4: EXPAND — add new child under C ===
        self.play(Indicate(phase_boxes[1], color=NM_GREEN, scale_factor=1.08), run_time=0.5)

        new_node = make_tree_node("D", NM_GREEN, radius=0.25)
        new_node.move_to(RIGHT * 1.8 + DOWN * 2.8)
        new_edge = Line(children[2].get_bottom(), new_node.get_top(), color=NM_GRID, stroke_width=1.5)

        self.play(Create(new_edge), FadeIn(new_node, scale=0.5), run_time=0.7)
        self.wait(0.4)

        # === Step 5: SIMULATE — random playout shown as dice ===
        self.play(Indicate(phase_boxes[2], color=NM_ORANGE, scale_factor=1.08), run_time=0.5)

        sim_label = Text("random playout...", font_size=16, color=NM_ORANGE)
        sim_label.next_to(new_node, RIGHT, buff=0.3)

        outcomes = ["W", "L", "W", "W"]
        outcome_texts = VGroup()
        for i, outcome in enumerate(outcomes):
            color = NM_GREEN if outcome == "W" else NM_PRIMARY
            t = Text(outcome, font_size=14, color=color)
            t.next_to(sim_label, RIGHT, buff=0.2 + i * 0.35)
            outcome_texts.add(t)

        self.play(FadeIn(sim_label), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(o, shift=UP * 0.1) for o in outcome_texts], lag_ratio=0.15),
            run_time=0.8,
        )
        self.wait(0.5)

        # === Step 6: BACKPROPAGATE — update stats along path ===
        self.play(Indicate(phase_boxes[3], color=NM_PRIMARY, scale_factor=1.08), run_time=0.5)

        # Flash path: D → C → R
        self.play(
            Flash(new_node, color=NM_YELLOW, line_length=0.2, flash_radius=0.4),
            run_time=0.4,
        )
        self.play(
            Flash(children[2], color=NM_YELLOW, line_length=0.2, flash_radius=0.4),
            run_time=0.4,
        )
        self.play(
            Flash(root, color=NM_YELLOW, line_length=0.2, flash_radius=0.4),
            run_time=0.4,
        )

        # Update stats
        new_stats = ["2/5", "1/3", "4/8"]
        for old_label, new_stat in zip(stat_labels, new_stats):
            new_label = Text(new_stat, font_size=12, color=NM_YELLOW)
            new_label.move_to(old_label.get_center())
            self.play(Transform(old_label, new_label), run_time=0.3)

        self.wait(0.8)

        # === Step 7: Summary — loop arrow ===
        loop_arrow = CurvedArrow(
            phase_boxes[3].get_bottom() + DOWN * 0.1,
            phase_boxes[0].get_bottom() + DOWN * 0.1,
            color=NM_YELLOW, stroke_width=2, angle=TAU / 6,
        )
        repeat_text = Text("repeat N iterations", font_size=14, color=NM_YELLOW)
        repeat_text.next_to(loop_arrow, DOWN, buff=0.1)

        self.play(Create(loop_arrow), FadeIn(repeat_text), run_time=0.7)
        self.wait(1.2)

        # Cleanup
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
