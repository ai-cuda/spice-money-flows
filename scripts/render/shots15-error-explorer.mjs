// Screenshot every row of prototypes/error-explorer.html (first variant) → <out>/row-NNN.png, plus the workbench.
import { createRequire } from 'module'; import { execSync } from 'child_process'; import path from 'path'; import { fileURLToPath } from 'url';
const { chromium } = createRequire(import.meta.url)(execSync('npm root -g').toString().trim() + '/playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const OUT = process.argv[2] || path.join(root, 'captures/prototype/15-error-explorer');
const only = process.argv[3] ? process.argv[3].split(',').map(Number) : null;
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2, locale: 'en-IN', timezoneId: 'Asia/Kolkata' });
const errs = []; p.on('pageerror', e => errs.push(e.message));
await p.goto('file://' + path.join(root, 'prototypes/error-explorer.html') + '#row-37'); await p.evaluate(() => document.fonts.ready);
await p.screenshot({ path: `${OUT}/00-workbench.png` });
const rows = only || await p.evaluate(() => [...document.querySelectorAll('#list button')].map(b => +b.dataset.r));
for (const r of rows) {
  await p.evaluate(r => window.__show(r, 0, false), r);
  await p.waitForTimeout(30);
  await p.locator('.phone').screenshot({ path: `${OUT}/row-${String(r).padStart(3, '0')}.png` });
}
console.log('rows', rows.length, 'pageerrors', errs.length, errs.slice(0, 3).join(' | ')); await b.close();
