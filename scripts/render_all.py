"""
Render all no-magic algorithm visualization scenes.

Usage:
    python scripts/render_all.py                           # all scenes, MP4 + GIF
    python scripts/render_all.py --full-only               # MP4s only (1080p60)
    python scripts/render_all.py --preview-only            # GIF previews only (480p15)
    python scripts/render_all.py --quality medium           # custom quality preset
    python scripts/render_all.py microattention            # single scene
    python scripts/render_all.py microattention microgpt   # multiple scenes
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCENES_DIR = Path(__file__).resolve().parent.parent / "scenes"
RENDERS_DIR = Path(__file__).resolve().parent.parent / "renders"
PREVIEWS_DIR = Path(__file__).resolve().parent.parent / "previews"

QUALITY_PRESETS = {
    "low": ["-ql"],
    "medium": ["-qm"],
    "high": ["-qh"],
    "production": ["-qp"],
}


def discover_scenes() -> dict[str, str]:
    """Scan scenes/ for scene files and extract scene class names."""
    scenes: dict[str, str] = {}
    for path in sorted(SCENES_DIR.glob("scene_*.py")):
        text = path.read_text()
        for line in text.splitlines():
            if line.startswith("class ") and "NoMagicScene" in line:
                class_name = line.split("(")[0].replace("class ", "").strip()
                key = path.stem.replace("scene_", "")
                scenes[key] = f"{path.stem}:{class_name}"
                break
    return scenes


def render_scene(
    scene_ref: str,
    quality: str = "production",
    gif: bool = False,
) -> bool:
    """Render a single scene with manim."""
    scene_file, scene_class = scene_ref.split(":")
    scene_path = SCENES_DIR / f"{scene_file}.py"

    cmd = ["manim", str(scene_path), scene_class, *QUALITY_PRESETS.get(quality, ["-qh"])]
    if gif:
        cmd.append("--format=gif")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAIL: {scene_ref}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Render no-magic visualization scenes")
    parser.add_argument("scenes", nargs="*", help="Scene names to render (default: all)")
    parser.add_argument("--full-only", action="store_true", help="MP4s only")
    parser.add_argument("--preview-only", action="store_true", help="GIF previews only")
    parser.add_argument("--quality", default="production", choices=QUALITY_PRESETS)
    args = parser.parse_args()

    all_scenes = discover_scenes()

    if args.scenes:
        targets = {k: v for k, v in all_scenes.items() if k in args.scenes}
        missing = set(args.scenes) - set(targets)
        if missing:
            print(f"Unknown scenes: {missing}", file=sys.stderr)
            sys.exit(1)
    else:
        targets = all_scenes

    RENDERS_DIR.mkdir(exist_ok=True)
    PREVIEWS_DIR.mkdir(exist_ok=True)

    failed: list[str] = []
    for name, ref in targets.items():
        print(f"==> {name}")

        if not args.preview_only:
            if not render_scene(ref, quality=args.quality):
                failed.append(name)
                continue

        if not args.full_only:
            if not render_scene(ref, quality="low", gif=True):
                failed.append(f"{name} (gif)")

    if failed:
        print(f"\nFailed: {failed}", file=sys.stderr)
        sys.exit(1)

    print(f"\nRendered {len(targets)} scenes.")


if __name__ == "__main__":
    main()
