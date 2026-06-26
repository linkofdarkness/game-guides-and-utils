# Phasmophobia

**Phasmophobia** is a cooperative ghost-hunting investigation game. Players use evidence, equipment, map knowledge, cursed possessions, and ghost behavior tells to identify the ghost and complete contract objectives.

Developed and published by **Kinetic Games**.

[Phasmophobia on Steam](https://store.steampowered.com/app/739630/Phasmophobia/)

## Guides and Knowledge Base

### [Knowledge Base](knowledge-base/index.md)

Structured markdown data used as the source material for a custom GPT focused on Phasmophobia. The files are generated from current-game wiki data and are organized for retrieval, summarization, and answer grounding rather than long-form reading.

- [Ghosts](knowledge-base/ghosts.md): ghost evidence, forced evidence, strengths, weaknesses, and behavior tells.
- [Evidence](knowledge-base/evidence.md): evidence types and ghost evidence matrix.
- [Equipment](knowledge-base/equipment.md): equipment purchase data, tiers, unlock levels, and compact mechanics.
- [Maps](knowledge-base/maps.md): map size, floors, rooms, exits, keys, hiding spots, and cursed possession spawn notes.
- [Cursed Possessions](knowledge-base/cursed-possessions.md): cursed item mechanics and effects.
- [Mechanics](knowledge-base/mechanics.md): compact gameplay and settings facts from current gameplay pages.
- [Sources](knowledge-base/sources.md): scanned page inventory and source URLs.

### [Knowledge Base Generator](scripts/build_phasma_kb.mjs)

Regenerates the markdown knowledge base from phasmophobia.fandom.com using MediaWiki API data. The generator scans main-namespace pages, filters version/update/history/old-content pages, and treats remaining content as current unless a page explicitly marks it as historical.

The repo-local agent skill for this workflow is [.agents/skills/rebuild-phasmophobia-kb](../../.agents/skills/rebuild-phasmophobia-kb/SKILL.md).

Current generated scope:

- 372 scanned main-namespace page titles.
- 163 included current pages after redirect/history filtering.
- 29 ghost pages.
- 21 equipment pages.
- 14 map pages.
- 11 evidence pages.
- 8 cursed possession pages.
- 30 gameplay/settings pages.

---

Game content, names, stats, and other material referenced in these guides are likely the intellectual property of Kinetic Games and/or its licensors. These guides and knowledge-base files are not affiliated with or endorsed by those rights holders.
