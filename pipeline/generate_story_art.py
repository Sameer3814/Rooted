#!/usr/bin/env python3
"""
generate_story_art.py — generate wide story-scene illustrations via the
Gemini API (gemini-3.1-flash-image), same model and API shape as
pipeline/generate_character_art.py.

Replaces the SDXL-on-Colab approach (pipeline/colab_story_art_sdxl.ipynb):
the free-tier Colab pipeline got a real community LoRA to land the target
"stylized 3D animation" look on character-centered scenes (David and
Goliath, the feeding of the 5,000, the lions' den all came out well), but
landscape/atmosphere-heavy scenes (Creation, the Flood, a wide Crucifixion
vista) kept reading as generic realistic matte-painting instead — reviewed
directly and rejected. Gemini already proved itself consistent across all
267 character portraits with zero style drift, so this switches story art
to the same model rather than continuing to fight LoRA inconsistency for
free. pipeline/curation/story_art_settings.json (the hand-picked scene
descriptions) and pipeline/import_story_art.py (Colab's two-machine
import step) are superseded by this for story art specifically — kept
around only as history/reference, not deleted, since the character
pipeline's own docs/DATA_MODEL.md entries document exactly this kind of
before/after.

Reads the API key from pipeline/.env.local (gitignored — see
pipeline/.env.local.example), same as generate_character_art.py.

Usage
-----
    py pipeline/generate_story_art.py --test story_david_and_goliath
        Generate ONE image for a single story as a connectivity/quality
        check. Saves to pipeline/.artscratch/ (gitignored), does NOT touch
        any data file. Run this first.

    py pipeline/generate_story_art.py --batch story_david_and_goliath ...
        Generate for real: resizes/compresses and saves to
        media/stories/<id>.jpg, and adds the id to
        data/story_illustrations.json (a flat manifest, same shape/shortcut
        as data/character_portraits.json — see that file's own history for
        why this isn't the full Media entity yet).
"""

import argparse
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request

from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(REPO_ROOT, "pipeline", ".env.local")
SCRATCH_DIR = os.path.join(REPO_ROOT, "pipeline", ".artscratch")
MEDIA_DIR = os.path.join(REPO_ROOT, "media", "stories")
STORIES_DATA = os.path.join(REPO_ROOT, "data", "stories.json")
MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "story_illustrations.json")
STORY_ART_SETTINGS = os.path.join(REPO_ROOT, "pipeline", "curation", "story_art_settings.json")

MODEL = "gemini-3.1-flash-image"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"

# Wide scenes are resized down to this width, matching import_story_art.py's
# own target — sharp enough for a discovery-card thumbnail or a future
# full-width detail-page use, without carrying a multi-MB source image.
TARGET_WIDTH = 960

# Appended verbatim to every story prompt, same lever as
# generate_character_art.py's STYLE_SUFFIX — one fixed string carries the
# style consistency across every story, not per-scene wording. Adapted for
# a wide multi-figure/landscape SCENE rather than a close-up portrait, and
# explicitly steered toward staying stylized even when a scene has no
# foreground character to "anchor" the look — the exact failure mode SDXL
# hit on Creation/the Flood/the Crucifixion's wide vista.
STYLE_SUFFIX = (
    "Richly rendered stylized 3D character-animation art style, in the "
    "polished feel of a modern animated feature film. Explicitly NOT "
    "photorealistic, NOT a photograph, NOT a realistic matte painting, NOT "
    "hyperrealistic — this applies to the environment and landscape "
    "elements (mountains, sky, water, clouds) just as much as to any "
    "figures present; a scene with no characters in the foreground should "
    "still read as stylized animated art, not a realistic digital "
    "painting. Warm, painterly cinematic lighting; soft, tactile shading "
    "with clean, simplified forms rather than photographic texture. "
    "Ancient Near Eastern biblical-era clothing and setting rendered "
    "respectfully and without caricature, when people are present. Wide "
    "establishing scene, full figures and environment both clearly "
    "visible, full color, cinematic widescreen framing, no text or "
    "watermarks."
)


def load_settings():
    if not os.path.exists(STORY_ART_SETTINGS):
        return {}
    with open(STORY_ART_SETTINGS, encoding="utf-8") as fh:
        settings = json.load(fh)
    settings.pop("_comment", None)
    return settings


def load_api_key():
    if not os.path.exists(ENV_FILE):
        raise SystemExit(
            "error: %s not found. Copy pipeline/.env.local.example to "
            "pipeline/.env.local and paste your real Gemini API key in." % ENV_FILE
        )
    with open(ENV_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == "GEMINI_API_KEY":
                value = value.strip()
                if not value or value == "paste-your-key-here":
                    raise SystemExit(
                        "error: pipeline/.env.local still has the placeholder value — "
                        "paste your real key in and save the file."
                    )
                return value
    raise SystemExit("error: GEMINI_API_KEY not found in %s" % ENV_FILE)


def generate_image(api_key, prompt):
    """Same response shape as generate_character_art.py's generate_image() —
    see that function's docstring for why the parsing looks the way it
    does (the docs' example response shape doesn't match reality)."""
    body = json.dumps({
        "model": MODEL,
        "input": [{"type": "text", "text": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit("error: Gemini API returned HTTP %d:\n%s" % (e.code, detail))

    for step in payload.get("steps", []):
        if step.get("type") != "model_output":
            continue
        for item in step.get("content", []):
            if item.get("type") == "image" and item.get("data"):
                mime = item.get("mime_type", "image/png")
                ext = "jpg" if "jpeg" in mime else mime.split("/")[-1]
                return base64.b64decode(item["data"]), ext

    os.makedirs(SCRATCH_DIR, exist_ok=True)
    dump_path = os.path.join(SCRATCH_DIR, "last_response.json")
    with open(dump_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("warning: no model_output image step found in the response.", file=sys.stderr)
    print("Full raw response written to %s for inspection." % dump_path, file=sys.stderr)
    raise SystemExit(1)


def find_story(story_id):
    with open(STORIES_DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    for s in data["stories"]:
        if s["id"] == story_id:
            return s
    raise SystemExit("error: no story with id %s in %s" % (story_id, STORIES_DATA))


def build_prompt(story, scene):
    return "%s (%s): %s. %s" % (story["title"], story["primaryReference"], scene, STYLE_SUFFIX)


def get_scene(settings, story_id):
    scene = settings.get(story_id)
    if not scene:
        raise SystemExit(
            "error: no scene description for %s in %s — add one before generating."
            % (story_id, STORY_ART_SETTINGS)
        )
    return scene


def cmd_test(story_ids):
    api_key = load_api_key()
    settings = load_settings()
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    for story_id in story_ids:
        story = find_story(story_id)
        scene = get_scene(settings, story_id)
        prompt = build_prompt(story, scene)
        print("--- %s ---" % story_id, file=sys.stderr)
        print("Prompt:\n  %s\n" % prompt, file=sys.stderr)
        print("Calling Gemini (%s)... this is a real, billed API call." % MODEL, file=sys.stderr)
        image_bytes, ext = generate_image(api_key, prompt)
        out_path = os.path.join(SCRATCH_DIR, "%s_test.%s" % (story_id, ext))
        with open(out_path, "wb") as fh:
            fh.write(image_bytes)
        print("wrote %s (%d bytes) -> %s\n" % (story_id, len(image_bytes), out_path), file=sys.stderr)


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return []
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save_manifest(ids):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(sorted(set(ids)), fh, indent=2)
        fh.write("\n")


def cmd_batch(story_ids):
    api_key = load_api_key()
    settings = load_settings()
    os.makedirs(MEDIA_DIR, exist_ok=True)
    manifest = set(load_manifest())
    produced = []
    for story_id in story_ids:
        story = find_story(story_id)
        scene = get_scene(settings, story_id)
        prompt = build_prompt(story, scene)
        print("--- %s ---" % story_id, file=sys.stderr)
        print("Calling Gemini (%s)... this is a real, billed API call." % MODEL, file=sys.stderr)
        image_bytes, _ext = generate_image(api_key, prompt)

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        scale = TARGET_WIDTH / w
        img2 = img.resize((TARGET_WIDTH, round(h * scale)), Image.LANCZOS)
        out_path = os.path.join(MEDIA_DIR, story_id + ".jpg")
        img2.save(out_path, "JPEG", quality=82, optimize=True)
        print("wrote %s -> %s (%dx%d)\n" % (story_id, out_path, img2.width, img2.height), file=sys.stderr)
        manifest.add(story_id)
        produced.append(story_id)

    if produced:
        save_manifest(list(manifest))
        print("%d image(s) generated, manifest now has %d id(s)." % (len(produced), len(manifest)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", metavar="STORY_ID", nargs="+", help="generate one or more test images, no data changes")
    group.add_argument("--batch", metavar="STORY_ID", nargs="+", help="generate for real: writes media/stories/ and data/story_illustrations.json")
    args = ap.parse_args()

    if args.test:
        cmd_test(args.test)
    elif args.batch:
        cmd_batch(args.batch)


if __name__ == "__main__":
    main()
