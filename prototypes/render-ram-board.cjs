// Exports the interactive concepts as a single static SVG sheet.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const directory = __dirname;
const html = fs.readFileSync(path.join(directory, 'ram-indicators.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const slider = { value: 67, addEventListener() {} };
const noop = { innerHTML: '', textContent: '' };
const document = {
  getElementById(id) { return id === 'usage' ? slider : noop; },
  querySelectorAll() { return []; }
};
const context = vm.createContext({ document, console });
vm.runInContext(script + '\n;globalThis.exportedConcepts = concepts;', context);
const concepts = context.exportedConcepts;

const W = 1600, H = 1100;
const cyan = '#70d4e8', bright = '#e7f1f4', muted = '#8aa5b1';
function esc(value) { return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function label(x, y, value, size, color = bright, weight = 500, family = 'IBM Plex Sans, Noto Sans, Arial, sans-serif', extra = '') {
  return `<text x="${x}" y="${y}" fill="${color}" font-family="${family}" font-size="${size}" font-weight="${weight}" ${extra}>${esc(value)}</text>`;
}
function icon(index, x, y, size, suffix) {
  const contents = concepts[index][3](67, `board-${index}-${suffix}`)
    .replace(/^<svg[^>]*>/, '')
    .replace(/<\/svg>$/, '');
  return `<g transform="translate(${x} ${y}) scale(${size / 120})">${contents}</g>`;
}

let out = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>
  <radialGradient id="page-glow" cx="51%" cy="-6%" r="88%"><stop stop-color="#244a5b"/><stop offset=".53" stop-color="#0d1c29"/><stop offset="1" stop-color="#0a1621"/></radialGradient>
  <radialGradient id="stage-glow"><stop stop-color="#1c3a4a"/><stop offset=".52" stop-color="#142d3b"/><stop offset="1" stop-color="#112634"/></radialGradient>
  <linearGradient id="card-gradient" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#17303e"/><stop offset="1" stop-color="#102330"/></linearGradient>
</defs>
<rect width="${W}" height="${H}" fill="url(#page-glow)"/>
${label(42, 45, 'ORBITAL', 12, cyan, 600, 'IBM Plex Mono, monospace', 'letter-spacing="2"')}
${label(118, 45, '/  INTERFACE STUDIES', 11, '#91aeba', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1.5"')}
${label(1558, 45, 'MEMORY TELEMETRY  ·  CONCEPT SHEET 01/10', 10, '#91aeba', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1.3" text-anchor="end"')}
${label(42, 126, 'RAM, ten ways', 57, bright, 550, 'IBM Plex Sans, Arial, sans-serif', 'letter-spacing="-3"')}
${label(465, 126, '.', 57, cyan, 550, 'IBM Plex Sans, Arial, sans-serif')}
${label(43, 162, 'Ten distinct visual directions for a compact memory indicator.', 15, '#a8bfca')}
${label(43, 184, 'Each is shown again at 44 px panel scale.', 15, '#a8bfca')}
<rect x="1250" y="85" width="308" height="110" rx="13" fill="#122a38" stroke="#365463"/>
${label(1268, 109, 'SIMULATED MEMORY LOAD', 10, '#9bb4be', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1.2"')}
${label(1540, 111, '67%', 20, cyan, 600, 'IBM Plex Mono, monospace', 'text-anchor="end"')}
<line x1="1270" y1="143" x2="1538" y2="143" stroke="#315262" stroke-width="5" stroke-linecap="round"/>
<line x1="1270" y1="143" x2="1449.6" y2="143" stroke="${cyan}" stroke-width="5" stroke-linecap="round"/>
<circle cx="1449.6" cy="143" r="8" fill="#d9f4f7" stroke="${cyan}" stroke-width="3"/>
${label(1270, 178, '0%', 10, '#7996a4', 400, 'IBM Plex Mono, monospace')}
${label(1404, 178, '10.7 / 16 GB', 10, '#7996a4', 400, 'IBM Plex Mono, monospace', 'text-anchor="middle"')}
${label(1538, 178, '100%', 10, '#7996a4', 400, 'IBM Plex Mono, monospace', 'text-anchor="end"')}`;

const gap = 14, cardW = 292, cardH = 388, firstX = 42, firstY = 219;
concepts.forEach(([name, tag, description], index) => {
  const x = firstX + index % 5 * (cardW + gap);
  const y = firstY + Math.floor(index / 5) * (cardH + gap);
  const stageX = x + 9, stageY = y + 47, stageW = cardW - 18, stageH = 174;
  const panelY = y + cardH - 53;
  out += `
  <g>
    <rect x="${x}" y="${y}" width="${cardW}" height="${cardH}" rx="14" fill="url(#card-gradient)" stroke="#294454"/>
    ${label(x + 17, y + 29, `${String(index + 1).padStart(2, '0')} / 10`, 11, cyan, 600, 'IBM Plex Mono, monospace', 'letter-spacing="1.4"')}
    ${label(x + cardW - 17, y + 29, tag, 9, '#7395a3', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1.1" text-anchor="end"')}
    <rect x="${stageX}" y="${stageY}" width="${stageW}" height="${stageH}" rx="9" fill="url(#stage-glow)"/>
    <circle cx="${x + cardW/2}" cy="${stageY + stageH/2}" r="79" fill="none" stroke="#90c5d0" stroke-opacity=".08"/>
    <line x1="${stageX}" y1="${stageY + stageH/2}" x2="${stageX + stageW}" y2="${stageY + stageH/2}" stroke="#90c5d0" stroke-opacity=".06"/>
    ${icon(index, x + 83, stageY + 24, 126, 'large')}
    ${label(x + 17, y + 252, name, 17, bright, 600)}
    ${label(x + 17, y + 274, description, 11, muted, 400)}
    <rect x="${x + 1}" y="${panelY}" width="${cardW - 2}" height="52" rx="0" fill="#0b1c29"/>
    <line x1="${x + 1}" y1="${panelY}" x2="${x + cardW - 1}" y2="${panelY}" stroke="#2a4350"/>
    <circle cx="${x + 23}" cy="${panelY + 26}" r="10" fill="none" stroke="#456273"/>
    ${label(x + 23, panelY + 30, '+', 12, '#9eb5c1', 400, 'Arial, sans-serif', 'text-anchor="middle"')}
    <line x1="${x + 43}" y1="${panelY + 16}" x2="${x + 43}" y2="${panelY + 36}" stroke="#35505e"/>
    <rect x="${x + 54}" y="${panelY + 4}" width="44" height="44" fill="#1b3646" stroke="#315263"/>
    ${icon(index, x + 55, panelY + 5, 42, 'small')}
    ${label(x + cardW - 17, panelY + 24, 'PANEL', 8, '#668594', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1" text-anchor="end"')}
    ${label(x + cardW - 17, panelY + 38, 'VIEW / 44PX', 8, '#668594', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1" text-anchor="end"')}
  </g>`;
});

out += `${label(42, 1071, 'ORBITAL / VISUAL EXPLORATION ONLY', 9, '#6f8d9c', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1.3"')}
${label(1558, 1071, 'ALL CONCEPTS SHOWN AT 44 PX PANEL SCALE', 9, '#9db5bf', 500, 'IBM Plex Mono, monospace', 'letter-spacing="1.3" text-anchor="end"')}</svg>`;
// Qt's SVG renderer drops numerals from this system's IBM Plex Mono weight files.
// Use a stable mono face for the downloadable sheet; the HTML keeps the theme font.
out = out.replace(/font-family="[^"]*Mono[^"]*"/g, 'font-family="DejaVu Sans Mono"')
  .replace(/font-family="(?!DejaVu Sans Mono")[^"]*"/g, 'font-family="DejaVu Sans"');
fs.writeFileSync(path.join(directory, 'ram-indicators.svg'), out);
