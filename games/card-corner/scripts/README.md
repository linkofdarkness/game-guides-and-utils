# Card Corner — guide scripts

Miscellaneous scripts used to generate the crafting guide from a local game install. They are not part of the game itself — just local tooling to refresh extracted data, markdown, and community-guide output under the game directory.

## Scripts

| Script | Purpose |
| --- | --- |
| `extract_loot.py` | Scan Unity assets for loot tables; write `extracts/` and `icons/` |
| `mermaid_add_icons.py` | Replace mermaid text nodes with icon image nodes in the crafting guide |
| `export_mermaid_diagrams.py` | Render mermaid blocks to `diagrams/*.png` |
| `markdown_to_steam_bbcode.py` | Convert the crafting guide markdown to community BBCode |

## Regenerating the guide

Run these from the **game directory**, not from `scripts/`.

### 1. Extract loot from a local build

Point at your game install folder or its `*_Data` folder:

```bash
python scripts/extract_loot.py "/path/to/Card Corner" --generate-guide
```

This writes `extracts/`, `icons/`, and (with `--generate-guide`) the crafting guide markdown.

To regenerate only the markdown from existing extracts:

```bash
python scripts/extract_loot.py --generate-guide-only
```

**How extraction works:** The script loads `data.unity3d` and walks `MonoBehaviour` assets using field-name conventions — `lootName` for items, `craftMaterial1`/`craftMaterial2` for recipes, `allItems` for pools, and `levelRanges` for drop tables. It does not depend on a specific assembly name.

### 2. Review the crafting guide (manual)

After extraction, check the generated markdown:

- Confirm ingredient and crafted-item tables look correct.
- Mermaid diagrams are generated as text nodes with `nodeSpacing: 80` to reduce label overlap.
- To use icon nodes inside mermaid diagrams instead:
  ```bash
  python scripts/mermaid_add_icons.py
  ```
  Re-run after regenerating the markdown if you use icon nodes.

### 3. Export mermaid diagrams to PNG (optional)

```bash
python scripts/export_mermaid_diagrams.py
```

Output goes to `diagrams/{item-slug}-diagram.png`. Use `--only "Ammo"` to export a single diagram.

Diagrams with icon image nodes need matching files in `icons/`. Text-only mermaid blocks export without icons.

### 4. Generate community BBCode

```bash
python scripts/markdown_to_steam_bbcode.py
```

Writes the BBCode crafting guide alongside the markdown source.

## Quick reference

```bash
python scripts/extract_loot.py "/path/to/Card Corner" --generate-guide
python scripts/mermaid_add_icons.py                  # optional
python scripts/export_mermaid_diagrams.py            # optional
python scripts/markdown_to_steam_bbcode.py
```
