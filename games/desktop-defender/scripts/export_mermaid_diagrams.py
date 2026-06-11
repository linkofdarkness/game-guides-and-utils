#!/usr/bin/env python3
"""Export mermaid craft-progression diagrams from guides/Crafting.md to PNG files."""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    raise SystemExit(1)

GAME_DIR = Path(__file__).resolve().parent.parent
CRAFTING_MD = GAME_DIR / "guides" / "Crafting.md"
DIAGRAMS_DIR = GAME_DIR / "diagrams"
ICONS_DIR = GAME_DIR / "icons"

HEADING_RE = re.compile(r"^### (.+)$")
IMG_NODE_RE = re.compile(
    r'(\s+\w+@\{ img: ")(\.\./icons/[^"]+)(", label: "[^"]+", pos: "[^"]+", h: \d+, constraint: "[^"]+" \})'
)
MERMAID_CONFIG = {"maxTextSize": 2000000}
MIN_VALID_PNG_BYTES = 5_000


def to_kebab(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", " ", ascii_name).strip().lower()
    return "-".join(slug.split()) or "item"


def parse_diagrams(markdown: str) -> list[tuple[str, str]]:
    lines = markdown.splitlines()
    diagrams: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        match = HEADING_RE.match(lines[i])
        if not match:
            i += 1
            continue
        title = match.group(1).strip()
        i += 1
        while i < len(lines) and lines[i].strip() != "```mermaid":
            if lines[i].startswith("### ") or lines[i].startswith("## "):
                break
            i += 1
        if i >= len(lines) or lines[i].strip() != "```mermaid":
            continue
        i += 1
        mermaid_lines: list[str] = []
        while i < len(lines) and lines[i].strip() != "```":
            mermaid_lines.append(lines[i])
            i += 1
        if mermaid_lines:
            diagrams.append((title, "\n".join(mermaid_lines) + "\n"))
        if i < len(lines):
            i += 1
    return diagrams


def icon_to_data_uri(icon_path: Path, *, export_size: int = 64) -> str:
    with Image.open(icon_path) as img:
        img = img.convert("RGBA").resize((export_size, export_size), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"


def embed_icons_for_export(mermaid: str, icons_dir: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        prefix, rel_path, suffix = match.groups()
        icon_path = icons_dir / Path(rel_path).name
        if not icon_path.is_file():
            raise FileNotFoundError(f"Missing icon for export: {icon_path}")
        return f"{prefix}{icon_to_data_uri(icon_path)}{suffix}"

    return IMG_NODE_RE.sub(replace, mermaid)


def mmdc_command() -> list[str]:
    npx = shutil.which("npx")
    if not npx:
        raise RuntimeError("npx not found on PATH (install Node.js)")
    return [npx, "--yes", "@mermaid-js/mermaid-cli"]


def render_diagram(mermaid: str, output_png: Path, mmdc_cmd: list[str]) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        temp_mmd = tmp_path / "diagram.mmd"
        temp_config = tmp_path / "config.json"
        temp_mmd.write_text(mermaid, encoding="utf-8")
        temp_config.write_text(json.dumps(MERMAID_CONFIG), encoding="utf-8")
        try:
            result = subprocess.run(
                [
                    *mmdc_cmd,
                    "-i",
                    str(temp_mmd),
                    "-o",
                    str(output_png),
                    "-b",
                    "transparent",
                    "-c",
                    str(temp_config),
                ],
                check=True,
                capture_output=True,
                text=True,
                shell=False,
            )
            if result.stdout.strip():
                print(result.stdout.strip())
        except subprocess.CalledProcessError as exc:
            print(exc.stderr or exc.stdout, file=sys.stderr)
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Export a single diagram by item name (e.g. Boson)")
    args = parser.parse_args()

    if not CRAFTING_MD.is_file():
        print(f"Missing {CRAFTING_MD}", file=sys.stderr)
        return 1

    mmdc_cmd = mmdc_command()
    diagrams = parse_diagrams(CRAFTING_MD.read_text(encoding="utf-8"))
    if args.only:
        diagrams = [(title, mermaid) for title, mermaid in diagrams if title == args.only]
        if not diagrams:
            print(f"No diagram found for {args.only!r}", file=sys.stderr)
            return 1
    elif not diagrams:
        print("No mermaid diagrams found.", file=sys.stderr)
        return 1

    for title, mermaid in diagrams:
        slug = to_kebab(title)
        output_png = DIAGRAMS_DIR / f"{slug}-diagram.png"
        print(f"{title} -> {output_png.name}")
        try:
            export_mermaid = embed_icons_for_export(mermaid, ICONS_DIR)
        except FileNotFoundError as exc:
            print(f"Skipping {title}: {exc}", file=sys.stderr)
            continue
        render_diagram(export_mermaid, output_png, mmdc_cmd)
        if output_png.stat().st_size < MIN_VALID_PNG_BYTES:
            print(
                f"Warning: {output_png.name} looks like a failed render "
                f"({output_png.stat().st_size} bytes)",
                file=sys.stderr,
            )

    print(f"Exported {len(diagrams)} diagram(s) to {DIAGRAMS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
