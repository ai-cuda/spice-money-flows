// Captures every state of prototypes/training-ticker-prototype.html (phone frame only).
import { createRequire } from 'module';
import { execSync } from 'child_process';
const pw = createRequire(import.meta.url)(execSync('npm root -g').toString().trim() + '/playwright');
const OUT = new URL('../../captures/prototype/13-training-ticker/', import.meta.url).pathname;
const URL_ = new URL('../../prototypes/training-ticker-prototype.html', import.meta.url).href;
const b = await pw.chromium.launch(); const p = await b.newPage({ viewport: { width: 1380, height: 980 }, deviceScaleFactor: 2, locale: 'en-IN', timezoneId: 'Asia/Kolkata' });
const errs = []; p.on('pageerror', e => errs.push(e.message));
let n = 0; const shot = async (name, keep) => { n++; await p.waitForTimeout(300); if (!keep) await p.evaluate(() => document.querySelectorAll('.scr .toast').forEach(e => e.remove())); await p.locator('.phone').screenshot({ path: OUT + String(n).padStart(2, '0') + '-' + name + '.png' }); };
const setRange = async (sel, v) => { await p.evaluate(([s, v]) => { const e = document.querySelector(s); e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }, [sel, String(v)]); };
const lat = v => setRange('#lat', v);
const view = async y => { await p.locator('.scr .view').first().evaluate((e, y) => e.scrollTop = y, y); };
const until = sel => p.waitForSelector(sel, { timeout: 30000 });
const idle = () => p.waitForSelector('.loading', { state: 'detached', timeout: 30000 });
const loaded = async () => { await p.waitForFunction(() => window.proto.st().ticker !== null || !document.querySelector('#flags').checked, null, { timeout: 30000 }); await p.waitForTimeout(200); };
const clock = async m => { await setRange('#clk', m); await loaded(); };
const mode = async m => { await p.evaluate(m => window.proto.setMode(m), m); await loaded(); };
const sess = async v => { await p.selectOption('#sess', v); await loaded(); };

await p.emulateMedia({ reducedMotion: 'reduce' }); await p.goto(URL_); await lat(150); await p.evaluate(() => document.fonts.ready); await loaded();

// ---- TODAY (v6.6.62) ----
await sess('none');
await shot('today-home-no-session-ticker-shown-all-day');
await view(600); await shot('today-home-scrolled-recharges-and-bills');
await view(0); await p.click('[data-a=tick]'); await idle(); await shot('today-tap-opens-academy');
await view(300); await shot('today-academy-certification');
await p.click('[data-a=home]'); await loaded();
await clock(360); await shot('today-0600-ticker-still-shown');
await clock(1320); await shot('today-2200-ticker-still-shown');
await clock(705);
await sess('sched'); await shot('today-1152-countdown-to-1500');
await p.click('[data-a=tick]'); await until('.jt'); await shot('today-join-training-dialog-before-start'); await p.click('.jt .abtn');
await clock(900); await shot('today-1500-live-join-now');
await p.click('[data-a=tick]'); await until('.ext'); await shot('today-join-now-opens-zoom-link');
await p.click('[data-a=home]'); await loaded();
await p.selectOption('#open', 'POPUP'); await loaded(); await p.click('[data-a=tick]'); await until('.jt'); await shot('today-join-now-popup-open-type'); await p.click('.jt .abtn'); await p.selectOption('#open', 'DIRECT'); await loaded();
await clock(1020); await shot('today-1700-after-session-back-to-academy-text');
await clock(705);
await sess('book'); await shot('today-uistate2-bookable');
await p.click('[data-a=tick]'); await until('.tmode'); await shot('today-training-mode-dialog');
await p.click('[data-a=book]'); await idle(); await p.waitForSelector('.toast'); await shot('today-book-now-interest-recorded', 1);
await p.click('[data-a=tick]'); await until('.tmode'); await shot('today-training-mode-dialog-booked'); await p.click('[data-a=academy]'); await idle(); await shot('today-go-to-academy');
await p.click('[data-a=home]'); await loaded();
await sess('none'); await p.uncheck('#acad'); await p.click('[data-a=tick]'); await until('.dlg'); await shot('today-academy-not-activated-alert'); await p.click('[data-a=close]'); await p.check('#acad');
await p.uncheck('#flags'); await loaded(); await shot('today-init-flags-off-ticker-gone'); await p.check('#flags'); await loaded();

// ---- PROPOSED (BRD) ----
await mode('proposed'); await sess('sched');
await clock(600); await shot('proposed-1000-outside-slot-hidden-second-fold-visible');
await view(600); await shot('proposed-1000-scrolled');
await view(0); await clock(870); await shot('proposed-1430-slot-opens-countdown');
await p.click('[data-a=tick]'); await until('.jt'); await shot('proposed-join-training-dialog'); await p.click('.jt .abtn');
await clock(900); await shot('proposed-1500-live-join-now');
await p.click('[data-a=tick]'); await until('.ext'); await shot('proposed-join-now-opens-zoom-link'); await p.click('[data-a=home]'); await loaded();
await clock(960); await shot('proposed-1600-slot-ends-hidden');
await sess('none'); await clock(900); await shot('proposed-1500-no-session-ticker-to-academy');
await p.click('[data-a=tick]'); await idle(); await shot('proposed-no-session-academy'); await p.click('[data-a=home]'); await loaded();
await p.evaluate(() => window.proto.setDays([true, true, true, false, true, false, false])); await loaded(); await shot('proposed-slot-not-on-thursday-hidden');
await p.evaluate(() => window.proto.setDays([true, true, true, true, true, false, false])); await loaded();
await p.selectOption('#from', '600'); await p.selectOption('#to', '1200'); await loaded(); await clock(705); await shot('proposed-slot-moved-1000-2000-shown-at-1152');
await p.selectOption('#from', '870'); await p.selectOption('#to', '960'); await loaded();
await p.uncheck('#foldsw'); await clock(600); await shot('proposed-1000-clean-no-markers'); await clock(900); await sess('sched'); await shot('proposed-1500-clean-no-markers'); await p.check('#foldsw');
await mode('today'); await clock(705); await sess('none'); await p.uncheck('#foldsw'); await shot('today-clean-no-markers'); await p.check('#foldsw');

await p.locator('.wrap').screenshot({ path: OUT + '00-workbench.png' });
console.log('shots', n, 'errors', JSON.stringify(errs)); await b.close();
