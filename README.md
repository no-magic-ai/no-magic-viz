# no-magic-viz

Manim-powered algorithm visualizations for the [no-magic](https://github.com/no-magic-ai/no-magic) project.

Every no-magic script gets an animated explainer — showing the algorithm's core mechanics in motion, not just in code.

## Setup

```bash
uv sync
```

## Rendering

```bash
# All scenes
uv run python scripts/render_all.py

# Single scene
uv run python scripts/render_all.py microgpt

# GIF previews only (for README embeds)
uv run python scripts/render_all.py --preview-only

# Full MP4s only (1080p60)
uv run python scripts/render_all.py --full-only
```

## Adding a New Scene

1. Create `scenes/scene_<algorithm>.py`
2. Inherit from `NoMagicScene` in `scenes/base.py`
3. Set `title_text` and `subtitle_text` class attributes
4. Implement the `animate()` method
5. Render: `uv run python scripts/render_all.py <algorithm>`

## Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Background | `#1a1a2e` | Scene background |
| Primary | `#e94560` | Highlights, titles |
| Blue | `#0f3460` | Secondary elements |
| Green | `#16c79a` | Success, positive |
| Text | `#eaeaea` | Body text |
| Grid | `#2a2a4a` | Grid lines, subtle |
| Yellow | `#f5c542` | Warnings, attention |
| Orange | `#e97d32` | Intermediate states |
| Purple | `#9b59b6` | Special elements |

## License

MIT
