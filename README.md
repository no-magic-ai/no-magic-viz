# no-magic-viz

Manim-powered algorithm visualizations for the [no-magic](https://github.com/no-magic-ai/no-magic) project.

Every no-magic script gets an animated explainer — showing the algorithm's core mechanics in motion, not just in code.

## Structure

```text
no-magic-viz/
├── scenes/          ← Manim source files
│   ├── base.py      ← Shared base class, color palette
│   ├── scene_microattention.py
│   ├── scene_microgpt.py
│   └── ...
├── previews/        ← GIF previews for README embedding (tracked)
├── renders/         ← Full MP4s (local only, not committed)
├── assets/          ← Branded video frames
├── scripts/
│   ├── render.sh    ← Batch render script (bash)
│   └── render_all.py ← Batch render script (Python)
└── pyproject.toml
```

## Setup

```bash
uv sync
```

## Rendering

All rendering happens locally before push. CI only runs lint and syntax checks.

```bash
# All scenes (MP4 + GIF)
bash scripts/render.sh

# Single scene
bash scripts/render.sh microattention

# GIF previews only (fast)
bash scripts/render.sh --preview-only

# Full MP4s only (1080p60)
bash scripts/render.sh --full-only

# Python alternative
uv run python scripts/render_all.py
uv run python scripts/render_all.py microgpt --preview-only
```

## Adding a New Scene

1. Create `scenes/scene_<algorithm>.py`
2. Inherit from `NoMagicScene` in `scenes/base.py`
3. Set `title_text` and `subtitle_text` class attributes
4. Implement the `animate()` method
5. Render locally: `bash scripts/render.sh <algorithm>`
6. Commit the GIF preview to `previews/`

## Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Background | `#1a1a2e` | Dark navy (GitHub dark mode) |
| Primary | `#e94560` | Red/coral — highlights, emphasis |
| Blue | `#0f3460` | Deep blue — secondary elements |
| Green | `#16c79a` | Active/flowing states |
| Text | `#eaeaea` | Light gray labels |
| Grid | `#2a2a4a` | Subtle guides and gridlines |
| Yellow | `#f5c542` | Tertiary accent |
| Orange | `#e97d32` | Tertiary accent |
| Purple | `#9b59b6` | Tertiary accent |

## License

MIT
