---
name: rebuild-phasmophobia-kb
description: Rebuild and validate the Phasmophobia markdown knowledge base used by a custom GPT. Use when updating games/phasmophobia/knowledge-base from phasmophobia.fandom.com, refreshing generated current-game data, checking source coverage, preserving user-authored observations, or preparing KB files for GPT upload/retrieval.
---

# Rebuild Phasmophobia Knowledge Base

## Overview

Regenerate the Phasmophobia custom GPT knowledge base from the local generator, then validate that the output stayed structured, current-game focused, and compatible with the repository layout.

## Workflow

1. Inspect the current state before changing files:
   - Run `git status --short` from the repository root.
   - Read `games/phasmophobia/README.md` and `games/phasmophobia/knowledge-base/index.md` for expected scope.
   - Check whether `games/phasmophobia/knowledge-base/observations.md` has user-authored notes. Treat it as manual content and preserve it.
2. Run the generator from the repository root:
   - Preferred command: `node games/phasmophobia/scripts/build_phasma_kb.mjs`.
   - If `node` is unavailable, use the bundled Node runtime exposed by the Codex workspace dependencies.
   - Network access is required because the script reads `https://phasmophobia.fandom.com/api.php`; request escalation when the sandbox blocks network access.
3. Validate generated files:
   - Confirm these generated files exist under `games/phasmophobia/knowledge-base`: `index.md`, `ghosts.md`, `evidence.md`, `equipment.md`, `maps.md`, `cursed-possessions.md`, `mechanics.md`, and `sources.md`.
   - Confirm `observations.md` still exists if it existed before generation.
   - Search generated markdown for obvious extraction leftovers: raw `{{`, `}}`, `[[`, `]]`, `File:`, empty table cells that indicate parser failure, and headings copied as list text.
   - Spot-check `ghosts.md`, `equipment.md`, and `maps.md`; these are the highest-risk files because they depend on templates and tables.
4. Review diffs:
   - Use `git diff -- games/phasmophobia` to inspect generated changes.
   - Treat broad data churn as acceptable only when it matches wiki updates or generator changes.
   - Do not overwrite or remove manual notes in `observations.md` unless the user explicitly asks.
5. Report the result:
   - Summarize changed KB files and any generator changes.
   - Mention whether validation passed and whether network access was required.
   - Call out suspicious source changes, parser gaps, or files that need manual review.

## Generator Notes

The authoritative script is `games/phasmophobia/scripts/build_phasma_kb.mjs`. It scans main-namespace pages through the MediaWiki API, excludes version/update/history/old/removed/planned pages, and writes the generated markdown into `games/phasmophobia/knowledge-base`.

The knowledge base is for custom GPT retrieval and answer grounding, so prefer compact factual markdown over prose. If the generator needs changes, keep output stable and structured: tables for matrices and inventories, short bullets for mechanics, source URLs near page-specific facts, and no copied history/trivia/gallery sections.

## Expected Files

- `knowledge-base/index.md`: scope, scan rules, file list, and counts.
- `knowledge-base/ghosts.md`: ghost evidence, forced evidence, strengths, weaknesses, and behavior tells.
- `knowledge-base/evidence.md`: evidence types and ghost evidence matrix.
- `knowledge-base/equipment.md`: purchase data, tiers, unlock levels, and compact mechanics.
- `knowledge-base/maps.md`: map facts, rooms, exits, keys, hiding spots, and cursed possession spawn notes.
- `knowledge-base/cursed-possessions.md`: cursed item mechanics and effects.
- `knowledge-base/mechanics.md`: compact gameplay/settings facts.
- `knowledge-base/sources.md`: scanned page inventory and source URLs.
- `knowledge-base/observations.md`: manual player observations; preserve across rebuilds.
