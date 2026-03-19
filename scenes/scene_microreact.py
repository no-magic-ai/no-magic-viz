"""
Scene: ReAct Reasoning Loop
Script: microreact.py
Description: Thought → Action → Observation reasoning cycle with tool use
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import NM_BLUE, NM_GREEN, NM_GRID, NM_ORANGE, NM_PRIMARY, NM_TEXT, NM_YELLOW, NoMagicScene
from manim import *


def make_react_box(label, color, width=2.0, height=0.7):
    """Create a labeled box for a ReAct phase."""
    box = RoundedRectangle(
        corner_radius=0.12, width=width, height=height,
        color=color, fill_opacity=0.2, stroke_width=2,
    )
    text = Text(label, font_size=20, color=color, weight=BOLD)
    return VGroup(box, text)


class ReActScene(NoMagicScene):
    title_text = "ReAct Reasoning Loop"
    subtitle_text = "Thought → Action → Observation — interleaved reasoning and acting"

    def animate(self):
        # === Step 1: Show the ReAct cycle diagram ===
        thought_box = make_react_box("Thought", NM_BLUE)
        action_box = make_react_box("Action", NM_GREEN)
        observation_box = make_react_box("Observation", NM_ORANGE)

        # Arrange in a triangle
        thought_box.move_to(UP * 1.5)
        action_box.move_to(DOWN * 0.5 + LEFT * 2.5)
        observation_box.move_to(DOWN * 0.5 + RIGHT * 2.5)

        self.play(
            FadeIn(thought_box, shift=DOWN * 0.2),
            FadeIn(action_box, shift=UP * 0.2),
            FadeIn(observation_box, shift=UP * 0.2),
            run_time=0.9,
        )

        # Arrows forming the cycle
        arrow_ta = Arrow(
            thought_box.get_bottom() + LEFT * 0.3, action_box.get_top(),
            buff=0.1, color=NM_GRID, stroke_width=2,
        )
        arrow_ao = Arrow(
            action_box.get_right(), observation_box.get_left(),
            buff=0.1, color=NM_GRID, stroke_width=2,
        )
        arrow_ot = Arrow(
            observation_box.get_top(), thought_box.get_bottom() + RIGHT * 0.3,
            buff=0.1, color=NM_GRID, stroke_width=2,
        )

        self.play(
            GrowArrow(arrow_ta), GrowArrow(arrow_ao), GrowArrow(arrow_ot),
            run_time=0.8,
        )
        self.wait(0.5)

        # === Step 2: Animate a reasoning trace ===
        trace_title = Text("Example Trace", font_size=18, color=NM_YELLOW, weight=BOLD)
        trace_title.to_edge(DOWN, buff=2.5)

        trace_steps = [
            ("Thought", "I need to find the capital of France", NM_BLUE),
            ("Action", "search('capital of France')", NM_GREEN),
            ("Observation", "Paris is the capital of France", NM_ORANGE),
            ("Thought", "The answer is Paris", NM_BLUE),
            ("Action", "finish('Paris')", NM_GREEN),
        ]

        self.play(Write(trace_title), run_time=0.4)

        # Fade out cycle diagram to make room
        cycle_group = VGroup(
            thought_box, action_box, observation_box,
            arrow_ta, arrow_ao, arrow_ot,
        )
        self.play(
            cycle_group.animate.scale(0.5).to_edge(UP, buff=0.3).to_edge(RIGHT, buff=0.5),
            run_time=0.7,
        )

        # Show trace entries one by one
        trace_entries = VGroup()
        y_pos = 1.5

        for phase, content, color in trace_steps:
            phase_label = Text(f"{phase}:", font_size=16, color=color, weight=BOLD)
            content_label = Text(content, font_size=14, color=NM_TEXT)
            entry = VGroup(phase_label, content_label).arrange(RIGHT, buff=0.3)
            entry.move_to(LEFT * 1.0 + UP * y_pos)
            entry.align_to(LEFT * 3.5, LEFT)
            trace_entries.add(entry)
            y_pos -= 0.6

            # Highlight corresponding box in mini cycle
            if phase == "Thought":
                target = cycle_group[0]
            elif phase == "Action":
                target = cycle_group[1]
            else:
                target = cycle_group[2]

            self.play(
                FadeIn(entry, shift=RIGHT * 0.2),
                Indicate(target, color=color, scale_factor=1.15),
                run_time=0.7,
            )
            self.wait(0.3)

        self.wait(0.5)

        # === Step 3: Show the REINFORCE training signal ===
        reward_label = Text("REINFORCE Training", font_size=18, color=NM_PRIMARY, weight=BOLD)
        reward_label.to_edge(DOWN, buff=1.5)

        reward_formula = MathTex(
            r"\nabla_\theta J = \mathbb{E}[R \cdot \nabla_\theta \log \pi(a|s)]",
            font_size=26, color=NM_YELLOW,
        )
        reward_formula.next_to(reward_label, DOWN, buff=0.2)

        self.play(Write(reward_label), run_time=0.5)
        self.play(Write(reward_formula), run_time=0.9)
        self.wait(0.5)

        # Show reward signal flowing back
        reward_arrow = Arrow(
            reward_formula.get_top(), trace_entries[-1].get_bottom(),
            buff=0.1, color=NM_PRIMARY, stroke_width=2,
        )
        reward_text = Text("reward = correct?", font_size=14, color=NM_PRIMARY)
        reward_text.next_to(reward_arrow, RIGHT, buff=0.15)

        self.play(GrowArrow(reward_arrow), FadeIn(reward_text), run_time=0.7)
        self.wait(0.3)

        # Flash all trace entries to show policy update
        self.play(
            *[Indicate(entry, color=NM_YELLOW, scale_factor=1.05) for entry in trace_entries],
            run_time=0.8,
        )

        # Final summary
        summary = Text(
            "Learn to reason by trial and error",
            font_size=20, color=NM_GREEN, weight=BOLD,
        )
        summary.to_edge(DOWN, buff=0.3)
        self.play(Write(summary), run_time=0.7)
        self.wait(1.2)

        # Cleanup
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.9)
