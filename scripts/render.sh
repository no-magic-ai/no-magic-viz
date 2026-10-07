#!/usr/bin/env bash
# Render no-magic algorithm scenes (scenes/scene_<name>.py) to validated outputs.
# Usage: bash scripts/render.sh [--preview-only | --full-only] [scene_name]
#
# Examples:
#   bash scripts/render.sh                    # every scene_*.py: MP4 + GIF preview
#   bash scripts/render.sh microattention     # one scene: MP4 + GIF preview
#   bash scripts/render.sh --preview-only     # GIF previews only
#   bash scripts/render.sh microgpt --full-only
#
# Outputs (paths are relative to the repository root, whatever the caller's cwd):
#   renders/<name>.mp4   1920x1080, 60 fps (full scene)
#   previews/<name>.gif  400x225, 10 fps, optimized palette (full scene)
#
# Every output is rendered into a fresh staging directory under media/, then
# decoded with `ffmpeg -xerror` and probed with ffprobe. A preview's duration must
# also match the 480p15 render it was made from. Only a scene whose
# selected outputs all pass is moved into renders/ and previews/. The first
# failure stops the batch with a nonzero exit; outputs promoted for earlier
# scenes and all other existing files are left in place.
set -euo pipefail

USAGE="usage: bash scripts/render.sh [--preview-only | --full-only] [scene_name]"

FULL_WIDTH=1920
FULL_HEIGHT=1080
FULL_RATE=60/1
PREVIEW_WIDTH=400
PREVIEW_HEIGHT=225
PREVIEW_FPS=10
PREVIEW_RATE=$PREVIEW_FPS/1
PREVIEW_SOURCE_WIDTH=854
PREVIEW_SOURCE_HEIGHT=480
PREVIEW_SOURCE_FPS=15
PREVIEW_SOURCE_RATE=$PREVIEW_SOURCE_FPS/1
# Resampling the 15 fps source to 10 fps can shift the GIF's end by up to one frame
# interval of each rate (100 ms + 67 ms, rounded up); anything further is a broken preview.
PREVIEW_TIMELINE_TOLERANCE_MS=$(((1000 + PREVIEW_FPS - 1) / PREVIEW_FPS + (1000 + PREVIEW_SOURCE_FPS - 1) / PREVIEW_SOURCE_FPS))

die() {
    echo "render.sh: error: $1" >&2
    exit 1
}

usage_error() {
    echo "render.sh: error: $1" >&2
    echo "$USAGE" >&2
    exit 2
}

script_path="${BASH_SOURCE[0]}"
case "$script_path" in
    */*) script_dir="${script_path%/*}" ;;
    *) script_dir=. ;;
esac
REPO_ROOT="$(cd "$script_dir/.." && pwd -P)"
cd "$REPO_ROOT"

SCENES_DIR="$REPO_ROOT/scenes"
PREVIEW_DIR="$REPO_ROOT/previews"
RELEASE_DIR="$REPO_ROOT/renders"
MEDIA_DIR="$REPO_ROOT/media"

# === Arguments: at most one mode flag and one scene name, in any order ===
mode=""
selector=""
for arg in "$@"; do
    case "$arg" in
        --preview-only | --full-only)
            [ -z "$mode" ] || usage_error "only one mode flag is allowed (got $mode and $arg)"
            mode="$arg"
            ;;
        -*) usage_error "unknown option: $arg" ;;
        *)
            [ -z "$selector" ] || usage_error "only one scene may be selected (got '$selector' and '$arg')"
            [[ "$arg" =~ ^[A-Za-z0-9_]+$ ]] || usage_error "invalid scene name: '$arg'"
            selector="$arg"
            ;;
    esac
done

render_full=true
render_preview=true
case "$mode" in
    --preview-only) render_full=false ;;
    --full-only) render_preview=false ;;
esac

# === Scene selection ===
if [ -n "$selector" ]; then
    [ -f "$SCENES_DIR/scene_$selector.py" ] || usage_error "unknown scene: $selector (no scenes/scene_$selector.py)"
    scene_files=("$SCENES_DIR/scene_$selector.py")
else
    shopt -s nullglob
    scene_files=("$SCENES_DIR"/scene_*.py)
    shopt -u nullglob
    [ "${#scene_files[@]}" -gt 0 ] || die "no scenes/scene_*.py files found"
fi

# Each scene file must define exactly one top-level class whose name ends in
# "Scene" (NoMagicScene subclasses and plain manim Scene subclasses alike).
scene_class() {
    local file="$1" line found=""
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ "$line" =~ ^class\ ([A-Za-z_][A-Za-z0-9_]*Scene)\( ]]; then
            [ -z "$found" ] || die "$file defines more than one *Scene class ($found, ${BASH_REMATCH[1]})"
            found="${BASH_REMATCH[1]}"
        fi
    done <"$file"
    [ -n "$found" ] || die "$file defines no top-level *Scene class"
    echo "$found"
}

scene_names=()
scene_classes=()
for scene_file in "${scene_files[@]}"; do
    name="${scene_file##*/scene_}"
    class_name="$(scene_class "$scene_file")"
    scene_names+=("${name%.py}")
    scene_classes+=("$class_name")
done

# === Preflight: every tool the selected outputs need, before any file changes ===
required_tools=(manim ffmpeg ffprobe)
[ "$render_preview" = false ] || required_tools+=(gifsicle)
missing_tools=""
for tool in "${required_tools[@]}"; do
    command -v "$tool" >/dev/null 2>&1 || missing_tools="$missing_tools $tool"
done
[ -z "$missing_tools" ] || die "missing required tools:$missing_tools"

# === Owned staging directory, removed on every exit path ===
mkdir -p "$MEDIA_DIR"
STAGE="$(mktemp -d "$MEDIA_DIR/render.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Render one scene to MP4 with the Cairo renderer; print the exact expected output path.
render_scene() {
    local name="$1" class_name="$2" quality="$3" quality_dir="$4"
    local media_dir="$STAGE/$name/$quality_dir"
    if ! manim render --renderer=cairo "$quality" --format mp4 --progress_bar none \
        --media_dir "$media_dir" "$SCENES_DIR/scene_$name.py" "$class_name" >&2; then
        die "manim failed for $name ($quality_dir)"
    fi
    local output="$media_dir/videos/scene_$name/$quality_dir/$class_name.mp4"
    [ -s "$output" ] || die "manim produced no video for $name at $output"
    echo "$output"
}

# Fully decode a file and check its probed stream against the expected mode.
# Sets validated_ms to the probed duration in whole milliseconds.
validated_ms=0
validate_media() {
    local file="$1" want_width="$2" want_height="$3" want_rate="$4"
    local log="$STAGE/validate.log" key value
    local width="" height="" rate="" frames="" duration=""

    [ -s "$file" ] || die "expected output is missing or empty: $file"
    if ! ffmpeg -nostdin -hide_banner -v error -xerror -i "$file" -f null - 2>"$log"; then
        printf '%s\n' "$(<"$log")" >&2
        die "decode failed: $file"
    fi
    if [ -s "$log" ]; then
        printf '%s\n' "$(<"$log")" >&2
        die "decode reported errors: $file"
    fi

    if ! ffprobe -v error -select_streams v:0 -count_frames \
        -show_entries stream=width,height,r_frame_rate,nb_read_frames:format=duration \
        -of default=noprint_wrappers=1 "$file" >"$STAGE/probe.txt" 2>"$log"; then
        printf '%s\n' "$(<"$log")" >&2
        die "ffprobe failed: $file"
    fi
    if [ -s "$log" ]; then
        printf '%s\n' "$(<"$log")" >&2
        die "ffprobe reported errors: $file"
    fi
    while IFS='=' read -r key value; do
        case "$key" in
            width) width="$value" ;;
            height) height="$value" ;;
            r_frame_rate) rate="$value" ;;
            nb_read_frames) frames="$value" ;;
            duration) duration="$value" ;;
        esac
    done <"$STAGE/probe.txt"

    if [ "$width" != "$want_width" ] || [ "$height" != "$want_height" ]; then
        die "$file is ${width}x$height, expected ${want_width}x$want_height"
    fi
    [ "$rate" = "$want_rate" ] || die "$file frame rate is '$rate', expected $want_rate"
    if ! [[ "$frames" =~ ^[0-9]+$ ]] || [ "$frames" -eq 0 ]; then
        die "$file has no decodable frames ('$frames')"
    fi
    if ! [[ "$duration" =~ ^[0-9]*\.?[0-9]+$ ]] || [[ "$duration" =~ ^[0.]+$ ]]; then
        die "$file has no positive duration ('$duration')"
    fi
    local whole="${duration%%.*}" fraction="000"
    [[ "$duration" != *.* ]] || fraction="${duration#*.}000"
    validated_ms=$((10#${whole:-0} * 1000 + 10#${fraction:0:3}))
    echo "  OK: ${file##*/} ${width}x$height $rate fps, $frames frames, ${duration}s"
}

# Convert the 480p15 render into a 400px, 10 fps, 128-color GIF, then optimize it.
optimize_gif() {
    local name="$1" source_mp4="$2" out_gif="$3"
    local palette_gif="$STAGE/$name/palette.gif"
    if ! ffmpeg -nostdin -hide_banner -v error -xerror -y -i "$source_mp4" \
        -vf "fps=$PREVIEW_FPS,scale=$PREVIEW_WIDTH:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=sierra2_4a" \
        "$palette_gif"; then
        die "ffmpeg palette conversion failed for $name"
    fi
    if ! gifsicle --optimize=3 --lossy=80 "$palette_gif" -o "$out_gif"; then
        die "gifsicle failed for $name"
    fi
}

# === Render, validate, then promote one scene at a time ===
for i in "${!scene_names[@]}"; do
    name="${scene_names[$i]}"
    class_name="${scene_classes[$i]}"
    echo "=== Rendering: $name ($class_name) ==="

    if [ "$render_full" = true ]; then
        staged_mp4="$(render_scene "$name" "$class_name" -qh 1080p60)"
        validate_media "$staged_mp4" "$FULL_WIDTH" "$FULL_HEIGHT" "$FULL_RATE"
    fi

    if [ "$render_preview" = true ]; then
        preview_mp4="$(render_scene "$name" "$class_name" -ql 480p15)"
        validate_media "$preview_mp4" "$PREVIEW_SOURCE_WIDTH" "$PREVIEW_SOURCE_HEIGHT" "$PREVIEW_SOURCE_RATE"
        source_ms=$validated_ms
        staged_gif="$STAGE/$name/$name.gif"
        optimize_gif "$name" "$preview_mp4" "$staged_gif"
        validate_media "$staged_gif" "$PREVIEW_WIDTH" "$PREVIEW_HEIGHT" "$PREVIEW_RATE"
        drift_ms=$((validated_ms - source_ms))
        if [ "${drift_ms#-}" -gt "$PREVIEW_TIMELINE_TOLERANCE_MS" ]; then
            die "$name.gif lasts ${validated_ms} ms but its 480p15 render lasts ${source_ms} ms (allowed difference ${PREVIEW_TIMELINE_TOLERANCE_MS} ms)"
        fi
    fi

    if [ "$render_full" = true ]; then
        mkdir -p "$RELEASE_DIR"
        mv -f "$staged_mp4" "$RELEASE_DIR/$name.mp4"
        echo "  MP4: renders/$name.mp4"
    fi
    if [ "$render_preview" = true ]; then
        mkdir -p "$PREVIEW_DIR"
        mv -f "$staged_gif" "$PREVIEW_DIR/$name.gif"
        echo "  GIF: previews/$name.gif"
    fi
    rm -rf "${STAGE:?}/$name"
done

echo ""
echo "Rendering complete: ${#scene_names[@]} scene(s)."
