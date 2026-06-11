#!/usr/bin/env python3
"""Convert mermaid text nodes to icon image nodes in the crafting guide markdown."""

from __future__ import annotations

import re
import sys
from pathlib import Path

GAME_DIR = Path(__file__).resolve().parent.parent
GUIDE = GAME_DIR / "guides" / "Crafting.md"

IMG_LINE_RE = re.compile(
    r'<img src="(\.\./icons/[^"]+)"[^>]*alt="([^"]*)"[^>]*/>\s*\*\*([^*]+)\*\*'
)
NODE_BRACKET_RE = re.compile(r'^(\s+)(\w+)\["([^"]+)"\]\s*$')
NODE_IMAGE_RE = re.compile(r'^(\s+)(\w+)@\{.*label:\s*"([^"]+)"')


def image_node(node_id: str, icon: str, label: str) -> str:
    escaped = label.replace('"', '\\"')
    return (
        f'  {node_id}@{{ img: "{icon}", label: "{escaped}", '
        f'pos: "b", h: 32, constraint: "on" }}'
    )


def section_icon_map(section_lines: list[str]) -> dict[str, str]:
    icons: dict[str, str] = {}
    for line in section_lines:
        match = IMG_LINE_RE.search(line)
        if match:
            icons[match.group(3).strip()] = match.group(1)
    return icons


def convert_mermaid_block(block: str, icons: dict[str, str]) -> str:
    out_lines: list[str] = []
    for line in block.splitlines():
        bracket = NODE_BRACKET_RE.match(line)
        if bracket:
            _indent, node_id, label = bracket.groups()
            icon = icons.get(label)
            if not icon:
                print(f"Warning: no icon for {label!r}", file=sys.stderr)
                out_lines.append(line)
                continue
            out_lines.append(image_node(node_id, icon, label))
            continue
        if NODE_IMAGE_RE.match(line):
            out_lines.append(line)
            continue
        out_lines.append(line)
    return "\n".join(out_lines)


def convert_guide(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    i = 0
    converted = 0

    while i < len(lines):
        line = lines[i]
        if line.strip() == "```mermaid":
            section_start = len(out) - 1
            while section_start >= 0 and not out[section_start].startswith("### "):
                section_start -= 1
            section_lines = out[section_start:] if section_start >= 0 else []
            icons = section_icon_map(section_lines)

            out.append(line)
            i += 1
            block_lines: list[str] = []
            while i < len(lines) and lines[i].strip() != "```":
                block_lines.append(lines[i])
                i += 1
            converted_block = convert_mermaid_block("\n".join(block_lines), icons)
            if converted_block:
                out.extend(converted_block.splitlines())
                converted += 1
            continue

        out.append(line)
        i += 1

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return converted


def main() -> int:
    if not GUIDE.is_file():
        print(f"Missing {GUIDE}", file=sys.stderr)
        return 1

    count = convert_guide(GUIDE)
    print(f"Updated {count} mermaid diagram(s) in {GUIDE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
