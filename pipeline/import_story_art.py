#!/usr/bin/env python3
"""
import_story_art.py — finish the loop on story illustrations generated
externally on Google Colab (pipeline/colab_story_art_sdxl.ipynb, SDXL on a
free-tier T4 GPU — no billed API calls, unlike generate_character_art.py's
Gemini pipeline).

Colab can't write directly into this repo, so the workflow is:
  1. Run the notebook in Colab, download story_art.zip.
  2. Unzip it into pipeline/.storyart_incoming/ (gitignored scratch dir),
     one <story_id>.png/.jpg per story.
  3. Run this script. It validates each story id against data/stories.json,
     resizes/compresses each image, saves it to media/stories/<id>.jpg, and
     updates data/story_illustrations.json (a flat manifest of story ids
     that have real art — same shape as data/character_portraits.json).
  4. Delete the now-processed files from pipeline/.storyart_incoming/ (this
     script does NOT do that automatically, to avoid silently deleting a
     failed/unwanted generation you haven't reviewed yet).

Usage
-----
    py pipeline/import_story_art.py
        Process every file currently in pipeline/.storyart_incoming/.
"""

import json
import os
import sys

from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCOMING_DIR = os.path.join(REPO_ROOT, "pipeline", ".storyart_incoming")
STORIES_DATA = os.path.join(REPO_ROOT, "data", "stories.json")
MEDIA_DIR = os.path.join(REPO_ROOT, "media", "stories")
MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "story_illustrations.json")

# Story scenes are wide (SDXL's 1216x832, ~3:2) unlike the square character
# portraits — resized down to a width that stays sharp in both the small
# discovery-card thumbnail and a future full-width detail-page use, without
# carrying the full ~1MB+ source PNG into the repo.
TARGET_WIDTH = 960


def load_valid_story_ids():
    with open(STORIES_DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    return {s["id"] for s in data["stories"]}


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return []
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save_manifest(ids):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(sorted(set(ids)), fh, indent=2)
        fh.write("\n")


def main():
    if not os.path.isdir(INCOMING_DIR):
        raise SystemExit(
            "error: %s not found. Unzip the Colab download there first "
            "(one <story_id>.png/.jpg per story)." % INCOMING_DIR
        )

    valid_ids = load_valid_story_ids()
    manifest = load_manifest()
    os.makedirs(MEDIA_DIR, exist_ok=True)

    processed, skipped = [], []
    for fname in sorted(os.listdir(INCOMING_DIR)):
        story_id, ext = os.path.splitext(fname)
        if ext.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        if story_id not in valid_ids:
            print("skipping %s: no such story id in data/stories.json" % fname, file=sys.stderr)
            skipped.append(fname)
            continue

        src_path = os.path.join(INCOMING_DIR, fname)
        img = Image.open(src_path).convert("RGB")
        w, h = img.size
        scale = TARGET_WIDTH / w
        img2 = img.resize((TARGET_WIDTH, round(h * scale)), Image.LANCZOS)
        out_path = os.path.join(MEDIA_DIR, story_id + ".jpg")
        img2.save(out_path, "JPEG", quality=82, optimize=True)
        processed.append(story_id)
        print("%s -> %s (%dx%d)" % (fname, out_path, img2.width, img2.height))

    if processed:
        save_manifest(list(manifest) + processed)
        print("\n%d image(s) processed, manifest now has %d id(s)." % (len(processed), len(set(manifest) | set(processed))))
    if skipped:
        print("%d file(s) skipped (see warnings above)." % len(skipped))
    if not processed and not skipped:
        print("Nothing to do — %s is empty." % INCOMING_DIR)


if __name__ == "__main__":
    main()
