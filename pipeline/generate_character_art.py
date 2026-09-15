#!/usr/bin/env python3
"""
generate_character_art.py — generate character portrait illustrations via the
Gemini API (gemini-3.1-flash-image) and wire them into the Media entity
(DATA_MODEL.md §2 "Media").

Reads the API key from pipeline/.env.local (gitignored — see
pipeline/.env.local.example), never from a command-line argument or an
environment variable set elsewhere, so the key never has to be typed into a
shell command.

Style consistency across many characters is the hard part, not generation
itself — every prompt gets the exact same STYLE_SUFFIX appended, verbatim,
so the ~90 portraits read as one illustrated set rather than 90 unrelated
images that happen to share a subject.

Usage
-----
    py pipeline/generate_character_art.py --test char_david
        Generate ONE image for a single character as a connectivity/quality
        check. Saves to pipeline/.artscratch/ (gitignored), does NOT touch
        any curation file. Run this first.

    py pipeline/generate_character_art.py --batch char_david char_ruth ...
        Generate portraits for the given characters for real: saves to
        media/, adds a Media record to pipeline/curation/media.json, and
        adds the mediaIds reference to each character in
        pipeline/curation/starter_pack.json. Run build_media.py and
        build_starter_pack.py afterward to propagate into data/.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(REPO_ROOT, "pipeline", ".env.local")
SCRATCH_DIR = os.path.join(REPO_ROOT, "pipeline", ".artscratch")
MEDIA_DIR = os.path.join(REPO_ROOT, "media")
STARTER_PACK_CURATION = os.path.join(REPO_ROOT, "pipeline", "curation", "starter_pack.json")
MEDIA_CURATION = os.path.join(REPO_ROOT, "pipeline", "curation", "media.json")

MODEL = "gemini-3.1-flash-image"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"

# Appended verbatim to every character prompt. This one fixed string is the
# main lever for making ~90 separate generations read as one illustrated
# set, not the per-character wording.
#
# v2 (2026-09-15 test round) — two deliberate changes from the original
# "warm storybook illustration" style, both explicitly requested:
#   1. A richer, more dimensional stylized-animation art direction — warm,
#      painterly, expressive — described by its QUALITIES only, never by
#      naming a specific studio or film, since leaning on a named
#      copyrighted franchise's style is a real IP concern for a public app.
#   2. A real, story-appropriate background (mountains, a temple court,
#      wherever the character's defining scene actually happens) instead
#      of the old deliberately-blank atmospheric wash — the previous
#      version avoided literal scenery on purpose, but the owner wants the
#      setting itself to help tell each character's story. Kept softly
#      rendered / shallow depth-of-field so it still reads as a backdrop,
#      not a competing second subject, once the portrait is cropped small.
STYLE_SUFFIX = (
    "Richly rendered stylized 3D character-animation art style, in the "
    "polished feel of a modern animated feature film. Explicitly NOT "
    "photorealistic, NOT a photograph, NOT a photo-illustration, NOT "
    "hyperrealistic — no individually rendered skin pores, no photographic "
    "skin texture, no camera lens/depth-of-field artifacts on the FACE "
    "itself (soft depth-of-field on the background behind them is still "
    "correct). Also not flat vector art. Simplified, softly stylized "
    "facial proportions typical of animated feature films — smooth "
    "stylized skin shading in flat warm tones rather than photographic "
    "texture, large expressive eyes, clean stylized hair rendered as "
    "defined clumps/strands rather than photographic individual hairs — "
    "this applies just as much to older, weathered, or bearded faces as "
    "to youthful ones; age should read through stylized proportions and "
    "expression, not through photographic realism. Warm, painterly "
    "cinematic lighting; expressive, dignified facial detail; soft, "
    "tactile shading on skin, hair, and fabric. Ancient Near Eastern "
    "biblical-era clothing rendered respectfully and without caricature. "
    "Portray the subject at the age "
    "and life-stage of their OWN defining story, not aged by genealogical "
    "titles in the description below (\"ancestor of\", \"mother of\", "
    "\"grandmother of\", etc. describe their significance to someone else's "
    "story, not their own age or appearance). CLOSE-UP HEAD-AND-SHOULDERS "
    "PORTRAIT — face and shoulders fill most of the frame, centered, facing "
    "forward or slightly turned, with the SETTING described below visible "
    "behind them, rendered with soft shallow depth-of-field (gently out of "
    "focus, warm and atmospheric) so it reads clearly as a backdrop and "
    "never competes with the subject's face. Square aspect ratio, no text "
    "or watermarks."
)

CHARACTER_ART_SETTINGS = os.path.join(REPO_ROOT, "pipeline", "curation", "character_art_settings.json")

# Per-character background setting — where their own defining story
# actually takes place. Curated by hand in pipeline/curation/
# character_art_settings.json (25 major characters as of 2026-09-15,
# DATA_MODEL.md item 90); characters not listed there fall back to a
# generic era-appropriate backdrop in build_prompt(). This is deliberately
# a small hand-picked file, not automated from Story data yet — setting
# selection (which of a character's many scenes is THE defining one) is
# a real creative judgment call, not mechanical.
def load_settings():
    if not os.path.exists(CHARACTER_ART_SETTINGS):
        return {}
    with open(CHARACTER_ART_SETTINGS, encoding="utf-8") as fh:
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
    """POST to the Gemini image-generation endpoint; return (raw image bytes,
    file extension inferred from the returned mime type).

    Real confirmed response shape (the docs' own example, {"output_image":
    {"data": ...}}, does NOT match what the API actually returns — found by
    dumping a real response, see git history):
        {"steps": [
            {"type": "thought", "signature": "..."},         # internal, skip
            {"type": "model_output", "content": [
                {"type": "image", "mime_type": "image/jpeg", "data": "<base64>"}
            ]}
        ]}
    `steps` can apparently contain more than one "thought" entry before the
    real output, so this searches for the model_output step / image content
    item by type rather than assuming a fixed index.
    """
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


def find_character(char_id):
    with open(STARTER_PACK_CURATION, encoding="utf-8") as fh:
        pack = json.load(fh)
    for c in pack["characters"]:
        if c["id"] == char_id:
            return c
    raise SystemExit("error: no character with id %s in %s" % (char_id, STARTER_PACK_CURATION))



# Expression direction (2026-09-15, batch 3+) — every character now gets
# an explicit emotional-tone instruction rather than leaving expression
# entirely to the model's own read of the roles/setting text. Caught by
# direct feedback: Paul, whose arc ends in triumph (persecutor -> apostle
# -> "I have fought the good fight"), had rendered with a flat/unhappy
# expression despite that being a positive-arc figure. The rule going
# forward: a character whose OWN arc resolves well (redemption, faith
# rewarded, a life that ends in vindication) reads warm/genuinely happy;
# a character defined by villainy or a story that indicts them (a
# persecutor who never repents, a betrayer, an oppressor) reads subtly
# stern/hard, never cartoonish; anyone else (most prophets mid-warning,
# figures whose story is tragic but not villainous, e.g. Saul or
# Absalom) reads calm and neutral/dignified. This is a per-character
# judgment call recorded in character_art_settings.json's "expression"
# field, same mechanism as "description" and "setting".
EXPRESSION_POSITIVE = "a warm, genuinely joyful expression, a real and unmistakable smile"
EXPRESSION_NEGATIVE = "a subtly stern, hardened expression -- tension in the brow, a hard set to the mouth -- dignified and human, not cartoonishly villainous or exaggerated"
EXPRESSION_NEUTRAL = "a calm, composed, neutral expression -- dignified, neither smiling nor stern"
EXPRESSION_MAP = {"positive": EXPRESSION_POSITIVE, "negative": EXPRESSION_NEGATIVE, "neutral": EXPRESSION_NEUTRAL}


def build_prompt(character, setting=None, description=None, expression=None):
    # `character["roles"]` is real app-facing Character data (shown to
    # users elsewhere in the app) — never edited just to steer image
    # generation. When a role phrase misleads the model (e.g. Samuel's
    # roles literally start with "heard God's voice as a boy," which
    # made every generation depict him as a child, not the elder prophet
    # he's popularly known as), the fix is an art-prompt-only
    # `description` override here, layered in ADDITION to roles, never a
    # change to the underlying curation data.
    roles = ", ".join(character.get("roles", [])) or "a figure from the Bible"
    text = description or roles
    setting = setting or "a softly blurred, warm atmospheric backdrop with no specific recognizable location"
    expression_text = EXPRESSION_MAP.get(expression, EXPRESSION_NEUTRAL)
    return "%s: %s. SETTING: %s. EXPRESSION: %s. %s" % (character["name"], text, setting, expression_text, STYLE_SUFFIX)


def cmd_test(char_ids):
    api_key = load_api_key()
    settings = load_settings()
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    for char_id in char_ids:
        character = find_character(char_id)
        entry = settings.get(char_id)
        # An entry is either a plain setting string, or {"setting":...,
        # "description":..., "expression":...} when the character also
        # needs a prompt-text override (see build_prompt()'s docstring).
        if isinstance(entry, dict):
            setting, description = entry.get("setting"), entry.get("description")
            expression = entry.get("expression")
        else:
            setting, description, expression = entry, None, None
        prompt = build_prompt(character, setting, description, expression)
        print("--- %s ---" % char_id, file=sys.stderr)
        print("Prompt:\n  %s\n" % prompt, file=sys.stderr)
        print("Calling Gemini (%s)... this is a real, billed API call." % MODEL, file=sys.stderr)
        image_bytes, ext = generate_image(api_key, prompt)
        out_path = os.path.join(SCRATCH_DIR, "%s_test.%s" % (char_id, ext))
        with open(out_path, "wb") as fh:
            fh.write(image_bytes)
        print("wrote %s (%d bytes) -> %s\n" % (char_id, len(image_bytes), out_path), file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", metavar="CHAR_ID", nargs="+", help="generate one or more test images, no curation changes")
    group.add_argument("--batch", metavar="CHAR_ID", nargs="+", help="generate for real (not yet implemented)")
    args = ap.parse_args()

    if args.test:
        cmd_test(args.test)
    elif args.batch:
        raise SystemExit("error: --batch isn't wired up yet — validate with --test first.")


if __name__ == "__main__":
    main()
