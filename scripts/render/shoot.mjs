// Screenshot rendered layout pages to PNG.
// Usage: node shoot.mjs <html_dir> <png_dir> [name ...]   (no names = every .html in html_dir)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';

const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch { pw = require(path.join(execSync('npm root -g').toString().trim(), 'playwright')); }

const [htmlDir, pngDir, ...names] = process.argv.slice(2);
fs.mkdirSync(pngDir, { recursive: true });
const list = names.length ? names : fs.readdirSync(htmlDir).filter(f => f.endsWith('.html')).map(f => f.slice(0, -5));
const browser = await pw.chromium.launch({ executablePath: fs.existsSync('/opt/pw-browsers/chromium') ? undefined : undefined });
const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
let ok = 0;
for (const n of list) {
  try {
    await page.goto('file://' + path.resolve(htmlDir, n + '.html'));
    await page.waitForSelector('body[data-done="1"]', { timeout: 8000 });
    const el = await page.$('#screen');
    const box = await el.boundingBox();
    await page.setViewportSize({ width: 360, height: Math.min(Math.ceil(box.height), 2400) });
    await el.screenshot({ path: path.join(pngDir, n + '.png') });
    ok++;
  } catch (e) { console.log('FAIL', n, e.message.split('\n')[0]); }
}
await browser.close();
console.log(`shot ${ok}/${list.length}`, errors.length ? 'page errors: ' + [...new Set(errors)].slice(0, 5).join(' | ') : '');
