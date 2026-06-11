#!/usr/bin/env python3
"""Convert guides/Crafting.md to Steam Community guide BBCode."""

from __future__ import annotations

import re
import sys
from pathlib import Path

GAME_DIR = Path(__file__).resolve().parent.parent
GUIDE = GAME_DIR / "guides" / "Crafting.md"
OUT = GAME_DIR / "guides" / "Crafting.steam.bbcode"

GAME_META = {
    "title": "Desktop Defender",
    "publisher": "Poysky Productions",
    "gameplay_guide_url": "https://steamcommunity.com/sharedfiles/filedetails/?id=3602435715",
}

IMG_RE = re.compile(
    r'<img src="\.\./icons/([^"]+)"[^>]*/>\s*([^|]+?)(?=\s*\||\s*$)',
)
NODE_BRACKET_RE = re.compile(r'^\s+(\w+)\["([^"]+)"\]\s*$')
NODE_IMAGE_RE = re.compile(r'^\s+(\w+)@\{[^}]*label:\s*"([^"]+)"')
EDGE_RE = re.compile(r"^\s+(\w+)\s*-->\s*(\w+)\s*$")


def parse_markdown_table(lines: list[str], start: int) -> tuple[list[str], list[list[str]], int]:
    headers = [cell.strip() for cell in lines[start].strip("|").split("|")]
    rows: list[list[str]] = []
    i = start + 2
    while i < len(lines) and lines[i].startswith("|"):
        rows.append([cell.strip() for cell in lines[i].strip("|").split("|")])
        i += 1
    return headers, rows, i


def cell_to_bbcode(cell: str, *, item_column: bool = False) -> str:
    cell = cell.strip()
    match = IMG_RE.search(cell)
    if match:
        content = f"[b]{match.group(2).strip()}[/b]"
    else:
        content = cell
    if item_column:
        return f"\n{content}"
    return content


def bbcode_td(cell: str, *, item_column: bool = False) -> list[str]:
    content = cell_to_bbcode(cell, item_column=item_column)
    if item_column:
        return ["[td]", content, "[/td]"]
    return [f"[td]{content}[/td]"]


def bbcode_table(headers: list[str], rows: list[list[str]]) -> str:
    parts = ["[table]"]
    parts.append("[tr]")
    for header in headers:
        parts.append(f"[th]{header}[/th]")
    parts.append("[/tr]")
    for row in rows:
        parts.append("[tr]")
        for col_idx, cell in enumerate(row):
            parts.extend(bbcode_td(cell, item_column=col_idx == 0))
        parts.append("[/tr]")
    parts.append("[/table]")
    return "\n".join(parts)


def parse_mermaid_graph(mermaid_lines: list[str]) -> tuple[dict[str, str], list[tuple[str, str]]]:
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    for line in mermaid_lines:
        edge = EDGE_RE.match(line)
        if edge:
            edges.append((edge.group(1), edge.group(2)))
            continue
        bracket = NODE_BRACKET_RE.match(line)
        if bracket:
            nodes[bracket.group(1)] = bracket.group(2)
            continue
        image = NODE_IMAGE_RE.match(line)
        if image:
            nodes[image.group(1)] = image.group(2)
    return nodes, edges


def collapse_graph(
    nodes: dict[str, str], edges: list[tuple[str, str]]
) -> tuple[set[str], set[tuple[str, str]]]:
    labels = set(nodes.values())
    label_edges: set[tuple[str, str]] = set()
    for src_id, dst_id in edges:
        if src_id in nodes and dst_id in nodes:
            label_edges.add((nodes[src_id], nodes[dst_id]))
    return labels, label_edges


def sort_key(name: str) -> str:
    return name.casefold()


def ingredient_list(labels: set[str], edges: set[tuple[str, str]], final: str) -> str:
    has_incoming = {dst for _, dst in edges}
    seen: set[str] = set()
    items: list[str] = []
    for label in sorted(
        (name for name in labels if name != final and name not in has_incoming),
        key=sort_key,
    ):
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        items.append(label)
    return ", ".join(items)


def progression_bbcode(title: str, mermaid_lines: list[str]) -> list[str]:
    nodes, edges = parse_mermaid_graph(mermaid_lines)
    labels, label_edges = collapse_graph(nodes, edges)
    ingredients = ingredient_list(labels, label_edges, title)
    return [
        f"[h2]{title}[/h2]",
        f"Ingredients: {ingredients}",
        "",
    ]


def collect_intro(lines: list[str]) -> list[str]:
    intro: list[str] = []
    for line in lines:
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            break
        if line.strip():
            intro.append(line.strip())
    return intro


def read_mermaid_block(lines: list[str], start: int) -> tuple[list[str], int]:
    i = start
    while i < len(lines) and lines[i].strip() != "```mermaid":
        if lines[i].startswith("### ") or lines[i].startswith("## "):
            return [], i
        i += 1
    if i >= len(lines) or lines[i].strip() != "```mermaid":
        return [], i
    i += 1
    mermaid_lines: list[str] = []
    while i < len(lines) and lines[i].strip() != "```":
        mermaid_lines.append(lines[i])
        i += 1
    if i < len(lines):
        i += 1
    return mermaid_lines, i


def convert_crafting(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    meta = GAME_META
    game_title = meta["title"]

    out.append(f"[h1]{game_title} — Crafting Guide[/h1]")
    out.append("")
    for paragraph in collect_intro(lines):
        out.append(paragraph)
    out.append("")
    out.append(
        f"For a detailed guide on gameplay and items I recommend vonekiller's "
        f"[url={meta['gameplay_guide_url']}]Simple Guide + Tips[/url]."
    )
    out.append("")
    out.append(
        "[i]Crafting reference derived from game data. Does not include drop rates, "
        "inventory advice, or full item stats. Game content is property of Conradical "
        f"Games, {meta['publisher']}, and/or their licensors. Not affiliated with or "
        "endorsed by those rights holders.[/i]"
    )
    out.append("")

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("## Table of contents"):
            out.append("[h2]Table of contents[/h2]")
            out.append("[list]")
            i += 1
            while i < len(lines) and not lines[i].startswith("##"):
                if not re.match(r"^\s*-\s+", lines[i]):
                    i += 1
                    continue
                item = re.sub(r"^\s*-\s+", "", lines[i])
                item = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", item).strip()
                out.append(f"[*]{item}")
                i += 1
            out.append("[/list]")
            out.append("")
            continue

        if line.startswith("## Craft progression"):
            out.append("[h2]Craft progression[/h2]")
            out.append(
                "Each recipe lists the source ingredients needed to craft the final item."
            )
            out.append("")
            i += 1
            while i < len(lines) and not lines[i].startswith("###"):
                i += 1
            while i < len(lines):
                if not lines[i].startswith("### "):
                    i += 1
                    continue
                title = lines[i][4:].strip()
                i += 1
                mermaid_lines, i = read_mermaid_block(lines, i)
                out.extend(progression_bbcode(title, mermaid_lines))
            break

        if line.startswith("## "):
            out.append(f"[h2]{line[3:].strip()}[/h2]")
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if (
                i < len(lines)
                and not lines[i].startswith("#")
                and not lines[i].startswith("|")
                and not lines[i].startswith("```")
            ):
                out.append(lines[i])
                i += 1
            out.append("")
            continue

        if line.startswith("| ") and i + 1 < len(lines) and lines[i + 1].startswith("| ---"):
            headers, rows, i = parse_markdown_table(lines, i)
            out.append(bbcode_table(headers, rows))
            out.append("")
            continue

        if line.startswith("# "):
            i += 1
            continue

        i += 1

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    if not GUIDE.is_file():
        print(f"Missing {GUIDE}", file=sys.stderr)
        return 1
    OUT.write_text(convert_crafting(GUIDE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
