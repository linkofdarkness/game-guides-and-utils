import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const API = 'https://phasmophobia.fandom.com/api.php';
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(SCRIPT_DIR, '..', 'knowledge-base');
const USER_AGENT = 'CodexPhasmaKB/1.0';

const SKIP_TITLE = /^(?:\d+\.)+\d+$|^Main Page$|^Phasmophobia Wiki$|^Site Map$|^Updates$|Update$|Removed Features|Planned updates|Glitches|Contests|Third-party tools|Map Concepts|Kinetic Games|Media$/i;
const SKIP_SECTION = /^(?:History|Trivia|Gallery|Notes|References|See also|Audio|Images?)$/i;

const pageCache = new Map();

async function api(params) {
  const url = `${API}?${new URLSearchParams({ format: 'json', ...params })}`;
  const res = await fetch(url, { headers: { 'User-Agent': USER_AGENT } });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${url}`);
  return res.json();
}

async function allPages() {
  const pages = [];
  let cont = {};
  for (;;) {
    const json = await api({
      action: 'query',
      list: 'allpages',
      apnamespace: '0',
      aplimit: '500',
      ...cont,
    });
    pages.push(...json.query.allpages.map((p) => p.title));
    if (!json.continue) break;
    cont = { apcontinue: json.continue.apcontinue, continue: json.continue.continue };
  }
  return pages;
}

async function page(title) {
  if (pageCache.has(title)) return pageCache.get(title);
  const json = await api({
    action: 'query',
    prop: 'revisions|categories',
    titles: title,
    rvslots: 'main',
    rvprop: 'content',
    cllimit: '100',
    redirects: '1',
  });
  const p = Object.values(json.query.pages)[0];
  const content = p?.revisions?.[0]?.slots?.main?.['*'] ?? '';
  const data = {
    title: p.title,
    pageid: p.pageid,
    url: `https://phasmophobia.fandom.com/wiki/${encodeURIComponent(p.title.replaceAll(' ', '_'))}`,
    categories: (p.categories ?? []).map((c) => c.title.replace(/^Category:/, '')),
    content,
  };
  pageCache.set(title, data);
  pageCache.set(data.title, data);
  return data;
}

function cleanWiki(value) {
  if (!value) return '';
  return value
    .replace(/<ref[^>]*>[\s\S]*?<\/ref>/gi, '')
    .replace(/<ref[^/>]*\/>/gi, '')
    .replace(/<br\s*\/?>/gi, '; ')
    .replace(/\[\[File:[^\]]+\]\]/gi, '')
    .replace(/\[\[(?:[^|\]]+\|)?([^\]]+)\]\]/g, '$1')
    .replace(/\{\{Control\|([^}]+)\}\}/gi, '$1')
    .replace(/\{\{(?:Main|See also|main)\|([^}]+)\}\}/gi, '$1')
    .replace(/\{\{[^{}]*\}\}/g, '')
    .replace(/(?:^|\n)\s*\*+\s*/g, '; ')
    .replace(/'''?/g, '')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .replace(/^;\s*/, '')
    .replace(/\s*;\s*/g, '; ')
    .trim();
}

function findTemplate(content, name) {
  const idx = content.search(new RegExp(`\\{\\{\\s*${name}\\b`, 'i'));
  if (idx < 0) return '';
  let depth = 0;
  for (let i = idx; i < content.length - 1; i++) {
    const two = content.slice(i, i + 2);
    if (two === '{{') {
      depth++;
      i++;
    } else if (two === '}}') {
      depth--;
      i++;
      if (depth === 0) return content.slice(idx, i + 1);
    }
  }
  return '';
}

const TEMPLATE_KEYS = {
  Ghost: ['title', 'image1', 'strength', 'weakness(es)', 'abiliti(es)', 'Evidence1', 'Evidence2', 'Evidence3'],
  'Equipment Template': [
    'tier i img', 'tier ii img', 'tier iii img', 'price', 'maxamount', 'uses', 'starter',
    'tier i level', 'tier ii level', 'tier iii level',
    'tier i description', 'tier i purpose', 'tier i ability',
    'tier ii description', 'tier ii purpose', 'tier ii ability',
    'tier iii description', 'tier iii purpose', 'tier iii ability',
  ],
  Location: ['img', 'imgcaption', 'mapsize', 'unlocklevel', 'floors', 'rooms', 'exits', 'faucets', 'videofeeds', 'keys', 'img rooms', 'img sanity', 'img temperatures'],
};

function parseTemplate(content, name, clean = true) {
  const tpl = findTemplate(content, name);
  const known = TEMPLATE_KEYS[name];
  if (known?.length) {
    const hits = [];
    for (const key of known) {
      const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const re = new RegExp(`\\|\\s*${escaped}\\s*=`, 'gi');
      for (const m of tpl.matchAll(re)) hits.push({ key, index: m.index, end: m.index + m[0].length });
    }
    hits.sort((a, b) => a.index - b.index);
    const fields = {};
    for (let i = 0; i < hits.length; i++) {
      const start = hits[i].end;
      const end = hits[i + 1]?.index ?? tpl.lastIndexOf('}}');
      const value = tpl.slice(start, end).trim();
      fields[hits[i].key] = clean ? cleanWiki(value) : value;
    }
    return fields;
  }
  const fields = {};
  let key = null;
  for (const raw of tpl.split(/\r?\n/)) {
    const m = raw.match(/^\s*\|\s*([^=]+?)\s*=\s*(.*)$/);
    if (m) {
      key = m[1].trim();
      fields[key] = m[2].trim();
    } else if (key) {
      fields[key] += `\n${raw}`;
    }
  }
  return clean ? Object.fromEntries(Object.entries(fields).map(([k, v]) => [k, cleanWiki(v)])) : fields;
}

function section(content, names) {
  const wanted = Array.isArray(names) ? names : [names];
  const lines = content.split(/\r?\n/);
  const chunks = [];
  let active = false;
  let level = 0;
  for (const line of lines) {
    const h = line.match(/^(=+)\s*(.*?)\s*\1\s*$/);
    if (h) {
      const title = cleanWiki(h[2]);
      const thisLevel = h[1].length;
      if (active && thisLevel <= level) active = false;
      if (wanted.some((n) => n.toLowerCase() === title.toLowerCase())) {
        active = true;
        level = thisLevel;
        continue;
      }
    }
    if (active) chunks.push(line);
  }
  return chunks.join('\n');
}

function factBullets(content, sectionNames, limit = 8) {
  const text = removeSkippedSections(section(content, sectionNames));
  const lines = [];
  for (const raw of text.split(/\r?\n/)) {
    if (/^\s*=+.*=+\s*$/.test(raw)) continue;
    if (/^\s*(?:\{\||\||!|\|-|\})/.test(raw)) continue;
    const clean = cleanWiki(raw.replace(/^\s*\*+\s*/, '').replace(/^\s*(?:File:)?[^|\n]+\.(?:png|jpg|jpeg|webp|ogg)\|/i, ''));
    if (!clean || clean.length < 15) continue;
    if (/^(File:|thumb|class=|Category:)/i.test(clean)) continue;
    if (SKIP_SECTION.test(clean)) continue;
    lines.push(clean.replace(/\.$/, ''));
  }
  return [...new Set(lines)].slice(0, limit);
}

function removeSkippedSections(content) {
  const lines = content.split(/\r?\n/);
  const keep = [];
  let skipLevel = 0;
  for (const line of lines) {
    const h = line.match(/^(=+)\s*(.*?)\s*\1\s*$/);
    if (h) {
      const lvl = h[1].length;
      const title = cleanWiki(h[2]);
      if (SKIP_SECTION.test(title)) {
        skipLevel = lvl;
        continue;
      }
      if (skipLevel && lvl <= skipLevel) skipLevel = 0;
    }
    if (!skipLevel) keep.push(line);
  }
  return keep.join('\n');
}

function evidenceName(value) {
  if (!value) return '';
  const alt = value.match(/alt=([^|\]]+)/i)?.[1];
  const link = value.match(/link=([^|\]]+)/i)?.[1];
  return cleanWiki(alt || link || value)
    .replace(' (Evidence)', '')
    .replace('D.O.T.S', 'D.O.T.S.')
    .replace('D.O.T.S..', 'D.O.T.S.')
    .replace(/^\}+|\}+$/g, '')
    .trim();
}

function parseWikiTables(content) {
  const tables = [];
  const re = /\{\|[\s\S]*?\n\|\}/g;
  for (const match of content.matchAll(re)) {
    const table = match[0];
    const rows = [];
    let headers = [];
    for (const rowText of table.split(/\n\|-\n/)) {
      const cells = rowText
        .split(/\n(?=[!|])/)
        .map((cell) => cell.replace(/^\{\|[^\n]*\n?/, '').replace(/\n?\|\}$/, '').trim())
        .filter(Boolean);
      if (!cells.length) continue;
      const parsed = [];
      for (const cell of cells) {
        const marker = cell[0];
        let body = cell.slice(1).trim();
        if (body.includes('!!')) {
          parsed.push(...body.split('!!').map(cleanWiki).filter(Boolean));
        } else if (body.includes('||')) {
          parsed.push(...body.split('||').map(cleanWiki).filter(Boolean));
        } else {
          body = body.replace(/^[^|]*\|/, '');
          parsed.push(cleanWiki(body));
        }
        if (marker === '!' && !headers.length) headers = parsed.filter(Boolean);
      }
      if (parsed.some(Boolean)) rows.push(parsed.filter(Boolean));
    }
    if (rows.length) tables.push({ headers, rows });
  }
  return tables;
}

function mdTable(headers, rows) {
  if (!headers.length || !rows.length) return '';
  const esc = (v) => String(v ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, '<br>');
  const width = headers.length;
  const norm = rows.map((r) => Array.from({ length: width }, (_, i) => r[i] ?? ''));
  return [
    `| ${headers.map(esc).join(' | ')} |`,
    `| ${headers.map(() => '---').join(' | ')} |`,
    ...norm.map((r) => `| ${r.map(esc).join(' | ')} |`),
  ].join('\n');
}

function heading(title, level = 2) {
  return `${'#'.repeat(level)} ${title}\n`;
}

function kvList(obj, keys) {
  return keys
    .filter((k) => obj[k])
    .map((k) => `- ${titleCase(k)}: ${obj[k]}`)
    .join('\n');
}

function titleCase(s) {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}

function bullets(items) {
  return items.length ? items.map((x) => `- ${x}`).join('\n') : '- No compact current-version facts extracted.';
}

function isVersionOrHistory(title) {
  return SKIP_TITLE.test(title) || /Update$/i.test(title);
}

async function main() {
  await fs.rm(OUT, { recursive: true, force: true });
  await fs.mkdir(OUT, { recursive: true });

  const titles = await allPages();
  const rawPages = [];
  for (const title of titles) {
    if (!isVersionOrHistory(title)) rawPages.push(await page(title));
  }
  const unique = [...new Map(rawPages.map((p) => [p.pageid, p])).values()]
    .filter((p) => p.pageid && !p.content.trim().startsWith('#REDIRECT'));

  const ghosts = unique.filter((p) => p.categories.includes('Ghosts') && findTemplate(p.content, 'Ghost')).sort((a, b) => a.title.localeCompare(b.title));
  const equipment = unique.filter((p) => (p.categories.includes('Equipment') || p.categories.includes('Starter Equipment')) && findTemplate(p.content, 'Equipment Template')).sort((a, b) => a.title.localeCompare(b.title));
  const maps = unique.filter((p) => p.categories.includes('Maps') && findTemplate(p.content, 'Location')).sort((a, b) => a.title.localeCompare(b.title));
  const evidencePages = unique.filter((p) => p.categories.includes('Evidence')).sort((a, b) => a.title.localeCompare(b.title));
  const coreMechanics = unique.filter((p) => ['Gameplay', 'Settings'].some((c) => p.categories.includes(c))).sort((a, b) => a.title.localeCompare(b.title));
  const cursedNames = new Set(['Cursed Possession', 'Haunted Mirror', 'Monkey Paw', 'Music Box', 'Ouija Board', 'Summoning Circle', 'Tarot Cards', 'Voodoo Doll']);
  const cursed = unique.filter((p) => cursedNames.has(p.title)).sort((a, b) => a.title.localeCompare(b.title));

  await writeIndex(titles, unique, { ghosts, equipment, maps, evidencePages, coreMechanics, cursed });
  await writeGhosts(ghosts);
  await writeEvidence(evidencePages, ghosts);
  await writeEquipment(equipment);
  await writeMaps(maps);
  await writeCursed(cursed);
  await writeMechanics(coreMechanics);
}

async function writeIndex(all, included, groups) {
  const lines = [
    '# Phasmophobia Knowledge Base',
    '',
    `Generated from phasmophobia.fandom.com on ${new Date().toISOString().slice(0, 10)}.`,
    '',
    'Scope rules:',
    '- Main-namespace wiki pages were scanned through the MediaWiki API.',
    '- Version pages, update pages, history, trivia, gallery, references, and explicitly old/removed/planned pages were excluded from the knowledge files.',
    '- Remaining content is treated as current unless the page explicitly marks it as historical.',
    '',
    'Files:',
    '- ghosts.md: ghost evidence, forced evidence, strengths, weaknesses, and behavior tells.',
    '- evidence.md: evidence types and ghost evidence matrix.',
    '- equipment.md: equipment purchase data, tiers, unlock levels, and compact mechanics.',
    '- maps.md: map size, floors, rooms, exits, keys, hiding spots, and cursed possession spawn notes.',
    '- cursed-possessions.md: cursed item mechanics and effects.',
    '- mechanics.md: compact gameplay/settings facts from current gameplay pages.',
    '- sources.md: scanned page inventory and source URLs.',
    '',
    'Group counts:',
    `- Scanned main-namespace page titles: ${all.length}`,
    `- Included current pages after redirect/history filtering: ${included.length}`,
    `- Ghost pages: ${groups.ghosts.length}`,
    `- Equipment pages: ${groups.equipment.length}`,
    `- Map pages: ${groups.maps.length}`,
    `- Evidence pages: ${groups.evidencePages.length}`,
    `- Cursed possession pages: ${groups.cursed.length}`,
    `- Gameplay/settings pages: ${groups.coreMechanics.length}`,
    '',
  ];
  await fs.writeFile(path.join(OUT, 'index.md'), `${lines.join('\n')}\n`);

  const sources = [
    '# Sources',
    '',
    'Current-page scan inventory:',
    '',
    ...included.map((p) => `- [${p.title}](${p.url}) (${p.categories.join(', ') || 'uncategorized'})`),
    '',
    'Skipped title classes:',
    '- Version/changelog pages.',
    '- Update/event/planned/removed/glitch/wiki/meta pages.',
    '- Redirect aliases after canonical page resolution.',
    '',
  ];
  await fs.writeFile(path.join(OUT, 'sources.md'), `${sources.join('\n')}\n`);
}

async function writeGhosts(ghosts) {
  const rows = [];
  const sections = ['Behaviour', 'Behavior', 'Activity', 'Abilities', 'Hunt', 'Miscellaneous'];
  const lines = ['# Ghosts', '', '## Evidence Matrix', ''];

  for (const p of ghosts) {
    const g = parseTemplate(p.content, 'Ghost');
    const raw = parseTemplate(p.content, 'Ghost', false);
    const ev = [raw.Evidence1, raw.Evidence2, raw.Evidence3].map(evidenceName).filter(Boolean);
    const forced = /'''<u>|<u>'''/.test(p.content) ? 'See evidence page' : '';
    rows.push([p.title, ev.join(', '), forced, cleanWiki(g.strength), cleanWiki(g['weakness(es)']), cleanWiki(g['abiliti(es)'])]);
  }
  lines.push(mdTable(['Ghost', 'Evidence', 'Forced evidence', 'Strength', 'Weakness', 'Abilities'], rows));
  lines.push('');

  for (const p of ghosts) {
    const g = parseTemplate(p.content, 'Ghost');
    const raw = parseTemplate(p.content, 'Ghost', false);
    const ev = [raw.Evidence1, raw.Evidence2, raw.Evidence3].map(evidenceName).filter(Boolean);
    lines.push(heading(p.title));
    lines.push(`Source: ${p.url}`);
    lines.push('');
    lines.push(`- Evidence: ${ev.join(', ') || 'Unknown'}`);
    if (g.strength) lines.push(`- Journal strength: ${g.strength}`);
    if (g['weakness(es)']) lines.push(`- Journal weakness: ${g['weakness(es)']}`);
    if (g['abiliti(es)']) lines.push(`- Ability summary: ${g['abiliti(es)']}`);
    lines.push('- Current behavior facts:');
    lines.push(bullets(factBullets(p.content, sections, 10)));
    lines.push('');
  }
  await fs.writeFile(path.join(OUT, 'ghosts.md'), `${lines.join('\n')}\n`);
}

async function writeEvidence(evidencePages, ghosts) {
  const lines = ['# Evidence', ''];
  const evidence = await page('Evidence');
  lines.push('## Types');
  lines.push('');
  lines.push(bullets(factBullets(evidence.content, 'Types of evidence', 10)));
  lines.push('');
  lines.push('## Ghost Evidence Matrix');
  lines.push('');
  const rows = ghosts.map((p) => {
    const raw = parseTemplate(p.content, 'Ghost', false);
    return [p.title, ...[raw.Evidence1, raw.Evidence2, raw.Evidence3].map(evidenceName).filter(Boolean)];
  });
  lines.push(mdTable(['Ghost', 'Evidence 1', 'Evidence 2', 'Evidence 3'], rows));
  lines.push('');
  lines.push('## Evidence Pages');
  lines.push('');
  for (const p of evidencePages) {
    lines.push(heading(p.title, 3));
    lines.push(`Source: ${p.url}`);
    lines.push('');
    lines.push(bullets(factBullets(p.content, ['Mechanics', 'Tips', 'Ghost evidence', 'Types of evidence'], 8)));
    lines.push('');
  }
  await fs.writeFile(path.join(OUT, 'evidence.md'), `${lines.join('\n')}\n`);
}

async function writeEquipment(equipment) {
  const lines = ['# Equipment', ''];
  const rows = [];
  for (const p of equipment) {
    const e = parseTemplate(p.content, 'Equipment Template');
    if (Object.keys(e).length) rows.push([p.title, e.price || '', e.maxamount || '', e.starter || '', e['tier i level'] || '0', e['tier ii level'] || '', e['tier iii level'] || '']);
  }
  lines.push(mdTable(['Item', 'Price', 'Max', 'Starter', 'Tier I level', 'Tier II level', 'Tier III level'], rows));
  lines.push('');
  for (const p of equipment) {
    const e = parseTemplate(p.content, 'Equipment Template');
    lines.push(heading(p.title));
    lines.push(`Source: ${p.url}`);
    lines.push('');
    if (Object.keys(e).length) {
      lines.push(kvList(e, ['price', 'maxamount', 'uses', 'starter', 'tier i level', 'tier ii level', 'tier iii level']));
      for (const tier of ['tier i', 'tier ii', 'tier iii']) {
        const desc = e[`${tier} description`];
        const purpose = e[`${tier} purpose`];
        const ability = e[`${tier} ability`];
        if (desc || purpose || ability) {
          lines.push('');
          lines.push(`### ${titleCase(tier)}`);
          if (desc) lines.push(`- Description: ${desc}`);
          if (purpose) lines.push(`- Use: ${purpose}`);
          if (ability) lines.push(`- Stats: ${ability}`);
        }
      }
    }
    const facts = factBullets(p.content, ['Mechanics', 'Usage', 'Tips', 'EMF Level 5'], 8);
    lines.push('');
    lines.push('### Mechanics');
    lines.push(bullets(facts));
    lines.push('');
  }
  await fs.writeFile(path.join(OUT, 'equipment.md'), `${lines.join('\n')}\n`);
}

async function writeMaps(maps) {
  const lines = ['# Maps', ''];
  const rows = [];
  for (const p of maps) {
    const loc = parseTemplate(p.content, 'Location');
    rows.push([p.title, loc.mapsize || '', loc.unlocklevel || '', loc.floors || '', loc.rooms || '', loc.exits || '', loc.keys || '']);
  }
  lines.push(mdTable(['Map', 'Size', 'Unlock level', 'Floors', 'Rooms', 'Exits', 'Keys'], rows));
  lines.push('');
  for (const p of maps) {
    const loc = parseTemplate(p.content, 'Location');
    lines.push(heading(p.title));
    lines.push(`Source: ${p.url}`);
    lines.push('');
    lines.push(kvList(loc, ['mapsize', 'unlocklevel', 'floors', 'rooms', 'exits', 'faucets', 'videofeeds', 'keys']));
    lines.push('');
    lines.push('### Layout And Hiding');
    lines.push(bullets(factBullets(p.content, ['Structure', 'Layout tips', 'Key hiding spots and strategies'], 12)));
    lines.push('');
    const cursedFacts = factBullets(p.content, 'Cursed Possession locations', 10);
    if (cursedFacts.length) {
      lines.push('### Cursed Possession Locations');
      lines.push(bullets(cursedFacts));
      lines.push('');
    }
  }
  await fs.writeFile(path.join(OUT, 'maps.md'), `${lines.join('\n')}\n`);
}

async function writeCursed(cursed) {
  const lines = ['# Cursed Possessions', ''];
  for (const p of cursed) {
    lines.push(heading(p.title));
    lines.push(`Source: ${p.url}`);
    lines.push('');
    lines.push(bullets(factBullets(p.content, ['Mechanics', 'Usage', 'Questions', 'Wishes', 'Cards', 'Effects', 'Related difficulty settings', 'Objectives and tasks'], 14)));
    lines.push('');
    for (const table of parseWikiTables(removeSkippedSections(p.content)).slice(0, 2)) {
      if (table.headers.length >= 2 && table.rows.length >= 2) {
        lines.push(mdTable(table.headers, table.rows.slice(1, 30)));
        lines.push('');
      }
    }
  }
  await fs.writeFile(path.join(OUT, 'cursed-possessions.md'), `${lines.join('\n')}\n`);
}

async function writeMechanics(coreMechanics) {
  const preferred = [
    'Activity', 'Bone Evidence', 'Challenge Mode', 'Contract', 'Controls', 'Daily and Weekly Tasks', 'Death',
    'Difficulty', 'Difficulty/Custom', 'Event Board', 'Experience', 'Favorite Room', 'Fuse Box', 'Ghost Event',
    'Ghost Room', 'Hiding Spots', 'Hunt', 'Interaction', 'Journal', 'Money', 'Objectives', 'Optional Objective',
    'Photo', 'Player', 'Roaming', 'Sanity', 'Setup Phase', 'Shop', 'Temperature', 'Training', 'Truck', 'Voice chat', 'Weather',
  ];
  const byTitle = new Map(coreMechanics.map((p) => [p.title, p]));
  const pages = preferred.map((t) => byTitle.get(t)).filter(Boolean);
  const lines = ['# Mechanics', ''];
  for (const p of pages) {
    lines.push(heading(p.title));
    lines.push(`Source: ${p.url}`);
    lines.push('');
    lines.push(bullets(factBullets(p.content, ['Mechanics', 'Difficulties', 'Summary Table', 'Rewards', 'Types', 'Overview', 'Usage'], 16)));
    const tables = parseWikiTables(removeSkippedSections(p.content)).filter((t) => t.headers.length >= 2 && t.rows.length >= 2).slice(0, 2);
    for (const table of tables) {
      lines.push('');
      lines.push(mdTable(table.headers, table.rows.slice(1, 25)));
    }
    lines.push('');
  }
  await fs.writeFile(path.join(OUT, 'mechanics.md'), `${lines.join('\n')}\n`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
