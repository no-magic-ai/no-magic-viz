"""
Shared base class and color palette for all no-magic algorithm visualization scenes.

Every scene inherits NoMagicScene and overrides animate() with algorithm-specific
animation logic. Branded start/end frames and algorithm title card are handled
by the base class.
"""
from pathlib import Path

from manim import *

# no-magic color palette — matches GitHub dark mode aesthetics
NM_BG = "#1a1a2e"
NM_PRIMARY = "#e94560"
NM_BLUE = "#0f3460"
NM_GREEN = "#16c79a"
NM_TEXT = "#eaeaea"
NM_GRID = "#2a2a4a"
NM_YELLOW = "#f5c542"
NM_ORANGE = "#e97d32"
NM_PURPLE = "#9b59b6"

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
START_FRAME = str(_ASSETS_DIR / "video_start_frame.png")
END_FRAME = str(_ASSETS_DIR / "video_end_frame.png")


class NoMagicScene(Scene):
    """Base scene with branded start/end frames and algorithm title card.

    Subclasses set title_text and subtitle_text as class attributes,
    then implement animate() for the algorithm-specific visualization.

    Frame sequence: branded start frame -> algorithm title -> animation -> branded end frame
    """

    title_text: str = "Algorithm"
    subtitle_text: str = "one-liner description"

    def construct(self):
        self.camera.background_color = NM_BG
        self.show_start_frame()
        self.show_title()
        self.animate()
        self.show_end_frame()

    def show_start_frame(self):
        """Display the branded start frame PNG for 2.5 seconds, then fade out."""
        if Path(START_FRAME).exists():
            img = ImageMobject(START_FRAME).scale_to_fit_width(config.frame_width)
            self.add(img)
            self.wait(2.5)
            self.play(FadeOut(img))
        else:
            self.wait(0.5)

    def show_title(self):
        """Display algorithm title and subtitle, then fade out."""
        title = Text(self.title_text, font_size=48, color=NM_TEXT)
        subtitle = Text(self.subtitle_text, font_size=24, color=NM_PRIMARY)
        group = VGroup(title, subtitle).arrange(DOWN, buff=0.4)
        self.play(FadeIn(group))
        self.wait(2)
        self.play(FadeOut(group))

    def show_end_frame(self):
        """Display the branded end frame PNG for 3 seconds."""
        if Path(END_FRAME).exists():
            img = ImageMobject(END_FRAME).scale_to_fit_width(config.frame_width)
            self.play(FadeIn(img))
            self.wait(3)
        else:
            self.wait(1)

    def animate(self):
        """Override in subclasses with algorithm-specific animation logic."""
        raise NotImplementedError("Subclasses must implement animate()")
