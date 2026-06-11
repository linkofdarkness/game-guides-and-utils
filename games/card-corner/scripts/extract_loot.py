#!/usr/bin/env python3
"""Extract loot tables from a Unity game install into extracts/ (and icons/)."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

try:
    import UnityPy
    from UnityPy.classes.PPtr import PPtr
    from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
    from UnityPy.tools.extractor import exportSprite
except ImportError:
    print("UnityPy is required: pip install UnityPy Pillow", file=sys.stderr)
    raise SystemExit(1)

GAME_DIR = Path(__file__).resolve().parent.parent
EXTRACTS_DIR = GAME_DIR / "extracts"
ICONS_DIR = GAME_DIR / "icons"
GUIDES_DIR = GAME_DIR / "guides"

PROFILE = {
    "unity_version": "2022.3.62f2",
    "rarity": {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Epic", 4: "Legendary", 5: "Crafted"},
    "stats": {
        0: "ChipMultiplier", 1: "FlatChips", 2: "BlindDuration", 3: "MaxHP", 4: "DiamondMult",
        5: "HeartMult", 6: "SpadeMult", 7: "ClubMult", 8: "Luck", 9: "HighCardMult",
        10: "PairMult", 11: "TwoPairMult", 12: "TripsMult", 13: "StraightMult", 14: "FlushMult",
        15: "FullHouseMult", 16: "QuadsMult", 17: "StraightFlushMult", 18: "RoyalFlushMult",
        19: "EmptySlotMult", 20: "CritChance", 21: "CritMultiplier", 22: "Overflow", 23: "Momentum",
        24: "Allow4CardFlush", 25: "Allow4CardStraight", 26: "RainbowMult", 27: "PeriodicMult",
        28: "PeriodicHPRegen", 29: "LowHealthMult", 30: "DamageTakenMult", 31: "SetMaxHP",
        32: "HighHealthMult", 33: "FlushHouseMult", 34: "FiveOfAKindMult", 35: "FlushFiveMult",
        36: "ItemSellBonus", 37: "JackMult", 38: "QueenMult", 39: "KingMult", 40: "AceMult",
        41: "BonusAfterHit",
    },
    "mod_types": {0: "Flat", 1: "Percent"},
    "limit_field": "maxCount",
    "has_description": False,
    "drop_table_field": "levelRanges",
}

GAME_META = {
    "title": "Card Corner",
    "developer": "Conradical Games",
    "publisher": "Assemble Entertainment GmbH",
    "forging_intro": (
        "After Rebirthing for the first time, you now unlock Forging. Clicking on this menu "
        "will allow you to combine two pieces of loot on the floor to make an even stronger "
        "piece of loot if they're part of a crafting recipe."
    ),
}


def to_kebab(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", " ", ascii_name).strip().lower()
    return "-".join(slug.split()) or "item"


def mermaid_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", to_kebab(name))


def find_unity_data_dir(search_root: Path) -> Path:
    """Locate a Unity *_Data folder under search_root using common install layout."""
    search_root = search_root.resolve()
    candidates: list[Path] = []

    if search_root.name.endswith("_Data") and (search_root / "data.unity3d").is_file():
        candidates.append(search_root)

    for child in sorted(search_root.iterdir()):
        if not child.is_dir() or not child.name.endswith("_Data"):
            continue
        if (child / "data.unity3d").is_file() and (child / "Managed").is_dir():
            candidates.append(child)

    if not candidates:
        raise FileNotFoundError(
            f"No Unity *_Data folder with data.unity3d found under {search_root}"
        )
    if len(candidates) > 1:
        names = ", ".join(c.name for c in candidates)
        print(f"Multiple *_Data folders found ({names}); using {candidates[0].name}")
    return candidates[0]


def unique_icon_filename(loot_name: str, used: set[str]) -> str:
    base = to_kebab(loot_name)
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def pptr_name(path_id: int, items_by_id: dict[int, dict]) -> str:
    if path_id in items_by_id:
        return items_by_id[path_id]["lootName"]
    return "" if path_id == 0 else f"[id:{path_id}]"


def format_stats(mods: list[dict]) -> str:
    if not mods:
        return ""
    parts = []
    for mod in mods:
        stat = PROFILE["stats"].get(mod.get("stat"), mod.get("stat"))
        value = mod.get("addValue", mod.get("value"))
        mod_type = PROFILE["mod_types"].get(mod.get("modType"), mod.get("modType"))
        suffix = ""
        if mod.get("handInterval") not in (None, 0, 5):
            suffix += f",every{mod['handInterval']}hands"
        if mod.get("timeInterval") not in (None, 0, 5, 5.0):
            suffix += f",every{mod['timeInterval']}s"
        if mod.get("healthThreshold") not in (None, 0, 0.3, 0.30000001192092896):
            suffix += f",hp<{mod['healthThreshold']}"
        building = (mod.get("specificBuildingId") or "").strip()
        if building:
            suffix += f",building={building}"
        parts.append(f"{stat}({mod_type}):{value}{suffix}")
    return " | ".join(parts)


def parse_drop_tables(tree: dict) -> list[dict]:
    tables = []
    for entry in tree.get("levelRanges", []) or []:
        weights = []
        for w in entry.get("rarityChances", []) or []:
            weights.append({
                "rarity": PROFILE["rarity"].get(w.get("rarity"), w.get("rarity")),
                "weight": w.get("weight", 0),
            })
        tables.append({
            "minLevel": entry.get("minLevel", 0),
            "maxLevel": entry.get("maxLevel", 0),
            "weights": weights,
        })
    return tables


def extract_icon(icon_ptr: dict, obj_reader, icons_dir: Path, filename: str) -> bool:
    path_id = icon_ptr.get("m_PathID", 0) if isinstance(icon_ptr, dict) else 0
    if not path_id:
        return False
    try:
        ptr = PPtr(
            assetsfile=obj_reader.assets_file,
            m_FileID=icon_ptr.get("m_FileID", 0),
            m_PathID=path_id,
        )
        sprite_obj = ptr.deref()
        if sprite_obj.type.name != "Sprite":
            return False
        exportSprite(sprite_obj, str(icons_dir / filename), ".png")
        return True
    except Exception as exc:
        print(f"  icon failed for {filename}: {exc}")
        return False


def extract_loot(data_dir: Path) -> None:
    data_bundle = data_dir / "data.unity3d"
    managed_dir = data_dir / "Managed"
    if not data_bundle.is_file():
        raise FileNotFoundError(f"Missing {data_bundle}")
    if not managed_dir.is_dir():
        raise FileNotFoundError(f"Missing {managed_dir}")

    EXTRACTS_DIR.mkdir(parents=True, exist_ok=True)
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    env = UnityPy.load(str(data_bundle))
    generator = TypeTreeGenerator(PROFILE["unity_version"])
    generator.load_local_dll_folder(str(managed_dir))
    env.typetree_generator = generator

    script_cache: dict[int, str] = {}
    loot_items: dict[int, dict] = {}
    loot_item_readers: dict[int, tuple] = {}
    loot_pools: list[dict] = []
    distributions: list[dict] = []

    for obj in env.objects:
        if obj.type.name != "MonoScript":
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        class_name = tree.get("m_ClassName", "")
        namespace = tree.get("m_Namespace", "")
        script_cache[obj.path_id] = f"{namespace}.{class_name}" if namespace else class_name

    drop_field = PROFILE["drop_table_field"]
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue

        script_ptr = tree.get("m_Script", {})
        script_id = script_ptr.get("m_PathID", 0) if isinstance(script_ptr, dict) else 0
        script_name = script_cache.get(script_id, "Unknown")

        if "lootName" in tree:
            item = {
                "pathId": obj.path_id,
                "script": script_name,
                "lootName": tree.get("lootName", ""),
                "rarity": PROFILE["rarity"].get(tree.get("rarity"), tree.get("rarity")),
                "unique": tree.get("unique", False),
                "limited": tree.get("limited", False),
                "limitCount": tree.get(PROFILE["limit_field"], 0),
                "craftMaterial1Id": (tree.get("craftMaterial1") or {}).get("m_PathID", 0),
                "craftMaterial2Id": (tree.get("craftMaterial2") or {}).get("m_PathID", 0),
                "statModifiers": tree.get("statModifiers", []),
                "iconFile": "",
            }
            if "requiresSecretHandsUnlock" in tree:
                item["requiresSecretHandsUnlock"] = tree.get("requiresSecretHandsUnlock", False)
            loot_items[obj.path_id] = item
            loot_item_readers[obj.path_id] = (obj, tree.get("icon"))
        elif "allItems" in tree:
            pool = {
                "pathId": obj.path_id,
                "script": script_name,
                "assetName": tree.get("m_Name", ""),
                "itemPathIds": [
                    item.get("m_PathID", 0)
                    for item in (tree.get("allItems", []) or [])
                    if isinstance(item, dict)
                ],
            }
            if "raritySettings" in tree:
                pool["raritySettings"] = [
                    {
                        "rarity": PROFILE["rarity"].get(rs.get("rarity"), rs.get("rarity")),
                        "displayName": rs.get("displayName", ""),
                        "evMultiplier": rs.get("evMultiplier", 0),
                    }
                    for rs in (tree.get("raritySettings", []) or [])
                ]
            loot_pools.append(pool)
        elif drop_field in tree and "lootName" not in tree and "allItems" not in tree:
            distributions.append({
                "pathId": obj.path_id,
                "script": script_name,
                "assetName": tree.get("m_Name", ""),
                "entries": parse_drop_tables(tree),
            })

    for item in loot_items.values():
        item["craftMaterial1"] = pptr_name(item.pop("craftMaterial1Id"), loot_items)
        item["craftMaterial2"] = pptr_name(item.pop("craftMaterial2Id"), loot_items)
        item["statModifiersFormatted"] = format_stats(item.get("statModifiers", []))

    for pool in loot_pools:
        pool["itemNames"] = [
            loot_items.get(pid, {}).get("lootName", f"[unresolved:{pid}]")
            for pid in pool["itemPathIds"]
        ]

    used_icon_names: set[str] = set()
    icons_exported = 0
    icons_missing = 0
    for path_id, item in loot_items.items():
        obj_reader, icon_ptr = loot_item_readers[path_id]
        icon_filename = unique_icon_filename(item["lootName"], used_icon_names)
        item["iconFile"] = f"icons/{icon_filename}.png"
        if extract_icon(icon_ptr, obj_reader, ICONS_DIR, icon_filename):
            icons_exported += 1
        else:
            item["iconFile"] = ""
            icons_missing += 1

    items_sorted = sorted(loot_items.values(), key=lambda x: x.get("lootName", ""))
    fieldnames = [
        "lootName", "rarity", "unique", "limited", "limitCount",
        "craftMaterial1", "craftMaterial2", "requiresSecretHandsUnlock",
        "iconFile", "statModifiersFormatted", "pathId", "script",
    ]

    csv_path = EXTRACTS_DIR / "loot_items.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in items_sorted:
            writer.writerow(item)

    pools_path = EXTRACTS_DIR / "loot_pools.json"
    pools_path.write_text(json.dumps(loot_pools, indent=2), encoding="utf-8")

    dist_path = EXTRACTS_DIR / "loot_distributions.json"
    dist_path.write_text(json.dumps(distributions, indent=2), encoding="utf-8")

    print(f"Unity data: {data_dir}")
    print(f"Loot items: {len(loot_items)}")
    print(f"Loot pools: {len(loot_pools)}")
    print(f"Distributions: {len(distributions)}")
    print(f"Icons exported: {icons_exported}")
    if icons_missing:
        print(f"Icons missing: {icons_missing}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {pools_path}")
    print(f"Wrote {dist_path}")
    print(f"Wrote icons to {ICONS_DIR}")


def load_items() -> list[dict]:
    path = EXTRACTS_DIR / "loot_items.csv"
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_recipes(items: list[dict]) -> dict[str, tuple[str, str]]:
    recipes: dict[str, tuple[str, str]] = {}
    for item in items:
        m1 = (item.get("craftMaterial1") or "").strip()
        m2 = (item.get("craftMaterial2") or "").strip()
        if m1 or m2:
            recipes[item["lootName"]] = (m1, m2)
    return recipes


def collect_chains(recipes: dict[str, tuple[str, str]]) -> list[list[str]]:
    used_as_material: set[str] = set()
    for m1, m2 in recipes.values():
        if m1:
            used_as_material.add(m1)
        if m2:
            used_as_material.add(m2)

    finals = sorted(name for name in recipes if name not in used_as_material)

    def expand(name: str, stack: set[str]) -> list[list[str]]:
        if name not in recipes:
            return [[name]]
        if name in stack:
            return [[name]]
        stack.add(name)
        m1, m2 = recipes[name]

        def append_crafted(prefix: list[str]) -> list[str]:
            path = prefix[:]
            if not path or path[-1] != name:
                path.append(name)
            return path

        if m1 and m1 == m2:
            chains = [append_crafted(sub) for sub in expand(m1, stack)]
        else:
            left_paths = expand(m1, stack) if m1 else [[]]
            right_paths = expand(m2, stack) if m2 else [[]]
            chains = []
            for left in left_paths:
                for right in right_paths:
                    path = []
                    for part in left + right:
                        if not path or path[-1] != part:
                            path.append(part)
                    chains.append(append_crafted(path))
        stack.remove(name)
        return chains

    all_chains: list[list[str]] = []
    for final in finals:
        for chain in expand(final, set()):
            all_chains.append(chain)
    return all_chains


def chain_recipe_mermaid(chain: list[str], recipes: dict[str, tuple[str, str]]) -> str:
    chain_set = set(chain)
    ordered: list[str] = []
    seen: set[str] = set()
    for node in chain:
        if node not in seen:
            seen.add(node)
            ordered.append(node)

    lines = [
        "%%{init: {'flowchart': {'nodeSpacing': 80}}}%%",
        "flowchart TD",
    ]
    for node in ordered:
        label = node.replace('"', "'")
        lines.append(f'  {mermaid_id(node)}["{label}"]')

    edges: set[tuple[str, str]] = set()
    for node in ordered:
        if node not in recipes:
            continue
        m1, m2 = recipes[node]
        for material in (m1, m2):
            if material and material in chain_set:
                edges.add((material, node))

    for src, dst in sorted(edges):
        lines.append(f"  {mermaid_id(src)} --> {mermaid_id(dst)}")
    return "\n".join(lines)


def icon_markdown(name: str) -> str:
    return (
        f'<img src="../icons/{to_kebab(name)}.png" width="24" height="24" '
        f'alt="{name}" /> {name}'
    )


def icon_line(name: str) -> str:
    return (
        f'<img src="../icons/{to_kebab(name)}.png" width="24" height="24" '
        f'alt="{name}" /> **{name}**'
    )


def generate_crafting_guide() -> None:
    items = load_items()
    recipes = build_recipes(items)
    used_materials: dict[str, set[str]] = defaultdict(set)
    for crafted, (m1, m2) in recipes.items():
        if m1:
            used_materials[m1].add(crafted)
        if m2:
            used_materials[m2].add(crafted)

    ingredients = sorted(used_materials.keys(), key=str.lower)
    crafted_names = sorted(recipes.keys(), key=str.lower)
    chains = collect_chains(recipes)

    finals: list[str] = []
    seen_chains: set[tuple[str, ...]] = set()
    unique_chains: list[list[str]] = []
    for chain in chains:
        key = tuple(chain)
        if key in seen_chains:
            continue
        seen_chains.add(key)
        unique_chains.append(chain)
        finals.append(chain[-1])

    finals_sorted = sorted(set(finals), key=str.lower)
    meta = GAME_META
    title = meta["title"]

    lines = [
        f"# {title} — Crafting Guide",
        "",
        f"A simple crafting guide for {title}, showing what items to hold onto for crafting and what ingredients create which items.",
        "",
        meta["forging_intro"],
        "",
        "⚠️Items must be on the ground to be used in crafting, items equipped in any loot loadout will not be usable and must be dropped.",
        "",
        "## Table of contents",
        "",
        "- [Ingredient items](#ingredient-items)",
        "- [Crafted items](#crafted-items)",
        "- [Craft progression](#craft-progression)",
    ]
    for final in finals_sorted:
        lines.append(f"  - [{final}](#{to_kebab(final)})")

    lines.extend([
        "",
        "## Ingredient items",
        "",
        "Hold onto these items when they appear — they are used as crafting ingredients.",
        "",
        "| Item | Used to craft |",
        "| --- | --- |",
    ])
    for name in ingredients:
        crafts = ", ".join(sorted(used_materials[name], key=str.lower))
        lines.append(f"| {icon_markdown(name)} | {crafts} |")

    lines.extend([
        "",
        "## Crafted items",
        "",
        "This is a list of items that must be crafted. Some of the items are used to further craft other items.",
        "",
        "| Crafted item | Ingredient 1 | Ingredient 2 |",
        "| --- | --- | --- |",
    ])
    for name in crafted_names:
        m1, m2 = recipes[name]
        lines.append(f"| {icon_markdown(name)} | {m1 or '—'} | {m2 or '—'} |")

    lines.extend([
        "",
        "## Craft progression",
        "",
        "Each diagram shows recipe steps for one path to a final crafted item. Arrows run from ingredients toward the item they combine into.",
        "",
    ])

    chains_by_final: dict[str, list[str]] = {}
    for chain in unique_chains:
        chains_by_final.setdefault(chain[-1], chain)

    for final in finals_sorted:
        chain = chains_by_final[final]
        seen_nodes: set[str] = set()
        lines.append(f"### {final}")
        lines.append("")
        for node in chain:
            if node in seen_nodes:
                continue
            seen_nodes.add(node)
            lines.append(icon_line(node))
        lines.append("")
        lines.append("```mermaid")
        lines.append(chain_recipe_mermaid(chain, recipes))
        lines.append("```")
        lines.append("")

    guide_path = GUIDES_DIR / "Crafting.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {guide_path}")
    print(f"  ingredients: {len(ingredients)}")
    print(f"  crafted: {len(crafted_names)}")
    print(f"  progression diagrams: {len(finals_sorted)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "game_dir",
        nargs="?",
        help="Path to game install folder or *_Data directory",
    )
    parser.add_argument(
        "--generate-guide",
        action="store_true",
        help="Regenerate guides/Crafting.md from extracts/loot_items.csv",
    )
    parser.add_argument(
        "--generate-guide-only",
        action="store_true",
        help="Only regenerate guides/Crafting.md (skip Unity extraction)",
    )
    args = parser.parse_args()

    if args.generate_guide_only or args.generate_guide:
        generate_crafting_guide()
        if args.generate_guide_only:
            return 0

    if not args.game_dir:
        parser.error("game_dir is required unless --generate-guide-only is used")

    data_dir = find_unity_data_dir(Path(args.game_dir))
    extract_loot(data_dir)
    if args.generate_guide:
        print()
        generate_crafting_guide()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
