"""Behavioral tests for scripts/render.sh.

Each test copies render.sh into a throwaway repository layout with small plain
manim scenes and runs it with real manim, ffmpeg, ffprobe and gifsicle. Faults
are injected only at the external tool boundary (a tool missing from PATH, or a
replacement optimizer/probe executable) and the assertions check the files the
script leaves behind.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDER_SH = REPO_ROOT / "scripts" / "render.sh"
SHELL_UTILITIES = ("mkdir", "mktemp", "mv", "rm")
MEDIA_TOOLS = ("manim", "ffmpeg", "ffprobe", "gifsicle")
TIMEOUT_SECONDS = 600


def _require(tool: str) -> str:
    path = shutil.which(tool)
    if path is None:
        raise RuntimeError(f"render tests require '{tool}' on PATH")
    return path


BASH = _require("bash")
TOOLS = {tool: _require(tool) for tool in SHELL_UTILITIES + MEDIA_TOOLS + ("head",)}

# Two seconds of animation, so a preview that drops content is detectable. The
# scene leaves scenes/scene_<name>.rendered behind once manim starts rendering it.
ANIMATED_SCENE = """from pathlib import Path

from manim import *


class Helper:
    pass


class {cls}Scene(Scene):
    def construct(self) -> None:
        Path(__file__).with_suffix(".rendered").touch()
        self.play(Create(Square(color=BLUE)), run_time=1.0)
        self.play(Rotate(self.mobjects[0], angle=PI / 2), run_time=1.0)
"""
FAILING_SCENE = """from manim import *


class {cls}Scene(Scene):
    def construct(self) -> None:
        raise RuntimeError("scene construction failed")
"""
STILL_SCENE = """from manim import *


class {cls}Scene(Scene):
    def construct(self) -> None:
        self.add(Square())
"""
TWO_CLASS_SCENE = """from manim import *


class {cls}Scene(Scene):
    def construct(self) -> None:
        self.play(Create(Square()))


class Other{cls}Scene(Scene):
    def construct(self) -> None:
        self.play(Create(Circle()))
"""


def digest_tree(root: Path) -> dict[str, str]:
    """Map every file under previews/, renders/ and media/ to its SHA-256."""
    digests: dict[str, str] = {}
    for top in ("previews", "renders", "media"):
        for path in sorted((root / top).rglob("*")):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def probe(path: Path) -> dict[str, str]:
    """Return width/height/r_frame_rate/nb_read_frames/duration of a media file."""
    result = subprocess.run(
        [
            TOOLS["ffprobe"],
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=width,height,r_frame_rate,nb_read_frames:format=duration",
            "-of",
            "default=noprint_wrappers=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines())
    decode = subprocess.run(
        [TOOLS["ffmpeg"], "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    if decode.returncode != 0 or decode.stderr:
        raise AssertionError(f"{path} does not decode cleanly: {decode.stderr}")
    return fields


class RenderScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="render-test-"))
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = self.tmp / "repo"
        self.outside = self.tmp / "elsewhere"
        self.outside.mkdir()
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy2(RENDER_SH, self.repo / "scripts" / "render.sh")
        (self.repo / "scenes").mkdir()
        (self.repo / "scenes" / "overview.py").write_text(ANIMATED_SCENE.format(cls="Overview"))
        for top in ("previews", "renders", "media"):
            (self.repo / top).mkdir()
        (self.repo / "media" / "unrelated.txt").write_bytes(b"unrelated media bytes")
        (self.repo / "previews" / "unrelated.gif").write_bytes(b"unrelated preview bytes")

    def add_scene(self, name: str, template: str) -> None:
        """Add scenes/scene_<name>.py plus previously published outputs for it."""
        cls = name.capitalize()
        (self.repo / "scenes" / f"scene_{name}.py").write_text(template.format(cls=cls))
        (self.repo / "previews" / f"{name}.gif").write_bytes(f"old {name} gif".encode())
        (self.repo / "renders" / f"{name}.mp4").write_bytes(f"old {name} mp4".encode())

    def tool_path(self, omit: tuple[str, ...] = (), replace: dict[str, str] | None = None) -> str:
        """Build a PATH holding only the script's tools, minus `omit`, with `replace` scripts."""
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        replacements = replace or {}
        for tool in SHELL_UTILITIES + MEDIA_TOOLS:
            if tool in omit:
                continue
            target = bin_dir / tool
            if tool in replacements:
                target.write_text(replacements[tool])
                target.chmod(0o755)
            else:
                target.symlink_to(TOOLS[tool])
        return str(bin_dir)

    def render(self, *args: str, path: str) -> subprocess.CompletedProcess[str]:
        """Run the copied render.sh from an unrelated cwd in its own process group."""
        process = subprocess.Popen(
            [BASH, str(self.repo / "scripts" / "render.sh"), *args],
            cwd=self.outside,
            env={**os.environ, "PATH": path},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
        return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)

    def changed_files(self, before: dict[str, str]) -> set[str]:
        after = digest_tree(self.repo)
        return {
            path for path in before.keys() | after.keys() if before.get(path) != after.get(path)
        }

    def assert_failed_without_changes(
        self, result: subprocess.CompletedProcess[str], before: dict[str, str], code: int = 1
    ) -> None:
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(self.changed_files(before), set(), result.stderr)
        self.assertEqual(sorted(p.name for p in (self.repo / "media").iterdir()), ["unrelated.txt"])

    def assert_nothing_rendered(self) -> None:
        self.assertEqual(sorted((self.repo / "scenes").glob("*.rendered")), [])

    def test_argument_errors_exit_before_any_change(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        self.add_scene("beta", ANIMATED_SCENE)
        path = self.tool_path()
        before = digest_tree(self.repo)
        for args in (
            ("--preview-only", "--full-only"),
            ("alpha", "--full-only", "--full-only"),
            ("--skip-optimize", "alpha"),
            ("alpha", "beta"),
            ("missing",),
            ("overview",),
            ("../scenes/scene_alpha",),
        ):
            with self.subTest(args=args):
                self.assert_failed_without_changes(self.render(*args, path=path), before, code=2)
                self.assert_nothing_rendered()

    def test_scene_with_two_scene_classes_is_rejected_before_rendering(self) -> None:
        self.add_scene("alpha", TWO_CLASS_SCENE)
        before = digest_tree(self.repo)
        self.assert_failed_without_changes(self.render("alpha", path=self.tool_path()), before)

    def test_missing_gifsicle_refuses_preview_render_without_changes(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        result = self.render("alpha", path=self.tool_path(omit=("gifsicle",)))
        self.assert_failed_without_changes(result, before)
        self.assert_nothing_rendered()

    def test_missing_ffprobe_refuses_full_only_render_without_changes(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        result = self.render("--full-only", "alpha", path=self.tool_path(omit=("ffprobe",)))
        self.assert_failed_without_changes(result, before)
        self.assert_nothing_rendered()

    def test_full_only_renders_validated_mp4_without_gifsicle(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        self.add_scene("beta", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        result = self.render("alpha", "--full-only", path=self.tool_path(omit=("gifsicle",)))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.changed_files(before), {"renders/alpha.mp4"})
        fields = probe(self.repo / "renders" / "alpha.mp4")
        self.assertEqual((fields["width"], fields["height"]), ("1920", "1080"))
        self.assertEqual(fields["r_frame_rate"], "60/1")
        self.assertAlmostEqual(float(fields["duration"]), 2.0, delta=0.2)
        self.assertEqual(sorted(p.name for p in (self.repo / "media").iterdir()), ["unrelated.txt"])

    def test_preview_only_publishes_complete_scene_gif(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        result = self.render("--preview-only", "alpha", path=self.tool_path())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.changed_files(before), {"previews/alpha.gif"})
        fields = probe(self.repo / "previews" / "alpha.gif")
        self.assertEqual((fields["width"], fields["height"]), ("400", "225"))
        self.assertEqual(fields["r_frame_rate"], "10/1")
        self.assertAlmostEqual(float(fields["duration"]), 2.0, delta=0.2)
        self.assertEqual(sorted(p.name for p in (self.repo / "media").iterdir()), ["unrelated.txt"])

    def test_renderer_failure_keeps_previous_outputs(self) -> None:
        self.add_scene("alpha", FAILING_SCENE)
        before = digest_tree(self.repo)
        self.assert_failed_without_changes(self.render("alpha", path=self.tool_path()), before)

    def test_scene_without_video_output_fails(self) -> None:
        self.add_scene("alpha", STILL_SCENE)
        before = digest_tree(self.repo)
        result = self.render("--preview-only", "alpha", path=self.tool_path())
        self.assert_failed_without_changes(result, before)

    def test_optimizer_failure_keeps_previous_preview(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        failing_gifsicle = "#!/bin/sh\nexit 1\n"
        path = self.tool_path(replace={"gifsicle": failing_gifsicle})
        self.assert_failed_without_changes(
            self.render("--preview-only", "alpha", path=path), before
        )

    def test_corrupt_optimizer_output_is_not_published(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        truncating_gifsicle = (
            "#!/bin/sh\n"
            f'"{TOOLS["gifsicle"]}" "$@" || exit $?\n'
            'for arg in "$@"; do out="$arg"; done\n'
            f'"{TOOLS["head"]}" -c 2000 "$out" > "$out.part" && '
            f'"{TOOLS["mv"]}" "$out.part" "$out"\n'
        )
        path = self.tool_path(replace={"gifsicle": truncating_gifsicle})
        self.assert_failed_without_changes(
            self.render("--preview-only", "alpha", path=path), before
        )

    def test_probe_failure_keeps_previous_preview(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        path = self.tool_path(replace={"ffprobe": "#!/bin/sh\nexit 1\n"})
        self.assert_failed_without_changes(
            self.render("--preview-only", "alpha", path=path), before
        )

    def test_batch_stops_at_first_failure_and_keeps_earlier_outputs(self) -> None:
        self.add_scene("alpha", ANIMATED_SCENE)
        self.add_scene("beta", FAILING_SCENE)
        self.add_scene("gamma", ANIMATED_SCENE)
        before = digest_tree(self.repo)
        result = self.render("--preview-only", path=self.tool_path())
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.changed_files(before), {"previews/alpha.gif"})
        self.assertEqual(probe(self.repo / "previews" / "alpha.gif")["width"], "400")
        self.assertEqual(sorted(p.name for p in (self.repo / "media").iterdir()), ["unrelated.txt"])


if __name__ == "__main__":
    unittest.main()
