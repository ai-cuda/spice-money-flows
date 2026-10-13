import pw from '/home/claude/.npm-global/lib/node_modules/playwright/index.js';
const OUT = '/home/claude/spice-money-flows/captures/prototype/09-education-fees/';
const b = await pw.chromium.launch(); const p = await b.newPage({ viewport: { width: 1380, height: 980 }, deviceScaleFactor: 2, locale: 'en-IN', timezoneId: 'Asia/Kolkata' });
const errs = []; p.on('pageerror', e => errs.push(e.message));
const URL = 'file:///home/claude/spice-money-flows/prototypes/bbps-education-fees-prototype.html';
let n = 0; const shot = async name => { n++; await p.waitForTimeout(250); await p.locator('.phone').screenshot({ path: OUT + String(n).padStart(2, '0') + '-' + name + '.png' }); };
const lat = async v => { await p.fill('#lat', String(v)); await p.dispatchEvent('#lat', 'input'); };
const scrollView = async y => { await p.locator('.scr .view').first().evaluate((e, y) => e.scrollTop = y, y); };
const MOB = '7982005594';
async function toEntry(billerIdx = 0) {
  await p.click('.tile.live'); await p.fill('#mob', MOB); await p.click('[data-a=cont]');
  await p.click('[data-a=pick] >> text="Delhi"'); await p.click('[data-a=pick] >> text="South Delhi"');
  await p.waitForSelector('[data-a=biller]'); await p.click('[data-a=biller] >> nth=' + billerIdx);
}
async function fillStudent() { await p.fill('#p0', 'SBPS/2019/0457'); await p.fill('#p1', '21/08/2014'); }

await p.goto(URL); await lat(200);
// --- main journey
await shot('home');
await scrollView(520); await shot('home-recharges-and-bills');
await p.click('.tile.live'); await shot('mobile-entry');
await p.fill('#mob', MOB); await shot('mobile-entry-customer-display');
await p.click('[data-a=cont]'); await shot('select-state');
await p.click('[data-a=pick] >> text="Delhi"'); await shot('select-city-delhi');
await lat(2500); await p.click('[data-a=pick] >> text="South Delhi"'); await p.waitForTimeout(500); await shot('loading-billers');
await p.waitForSelector('[data-a=biller]'); await lat(200); await shot('select-institute');
await p.click('[data-a=biller] >> nth=0'); await shot('student-details');
await fillStudent(); await shot('student-details-filled');
await lat(2500); await p.click('[data-a=fetch]'); await p.waitForTimeout(500); await shot('fetching-fee');
await p.waitForSelector('#amt', { timeout: 15000 }); await lat(200); await shot('fee-details');
await p.click('details summary'); await scrollView(260); await shot('fee-details-view-more');
await p.click('[data-a=pay]'); await p.waitForSelector('[data-a=confirm]'); await shot('confirm-payment');
await p.click('[data-a=slab]'); await shot('ccf-slab');
await p.click('[data-a=backconfirm]'); await lat(2500); await p.click('[data-a=confirm]'); await p.waitForTimeout(500); await shot('processing-payment');
await p.waitForSelector('.view .spin', { timeout: 15000 }); await p.waitForTimeout(400); await shot('receipt-processing');
await p.waitForSelector('.rh', { timeout: 15000 }); await lat(200); await shot('receipt-success');
await scrollView(600); await shot('receipt-success-share');
// --- branches
const fresh = async () => { await p.click('#reset'); await lat(200); };
await fresh(); await p.uncheck('#enabled'); await p.click('.tile.live'); await shot('branch-bbps-not-enabled'); await p.check('#enabled');
await fresh(); await p.selectOption('#fetch', 'none'); await toEntry(); await fillStudent(); await p.click('[data-a=fetch]'); await p.waitForSelector('.dlg'); await shot('branch-no-fee-due'); await p.selectOption('#fetch', 'due');
await fresh(); await toEntry(); await fillStudent(); await p.click('[data-a=fetch]'); await p.waitForSelector('#amt'); await p.fill('#amt', '10000'); await p.click('[data-a=pay]'); await p.waitForSelector('.toast'); await shot('branch-amount-below-fee');
await fresh(); await p.selectOption('#bal', '6200'); await toEntry(); await fillStudent(); await p.click('[data-a=fetch]'); await p.waitForSelector('#amt'); await p.click('[data-a=pay]'); await p.waitForSelector('[data-a=confirm]'); await p.click('[data-a=confirm]'); await p.waitForSelector('[data-a=addbal]'); await shot('branch-low-wallet-balance'); await p.selectOption('#bal', '52000');
await fresh(); await lat(1500); await toEntry(); await fillStudent(); await p.check('input[name=pm][value=UPI]'); await p.click('[data-a=fetch]'); await p.waitForSelector('#amt', { timeout: 15000 }); await p.click('[data-a=pay]'); await p.waitForSelector('[data-a=confirm]', { timeout: 15000 }); await p.click('[data-a=confirm]'); await p.waitForSelector('.qr'); await shot('branch-upi-customer-qr'); await lat(200);
await fresh(); await p.selectOption('#out', '001'); await toEntry(); await fillStudent(); await p.click('[data-a=fetch]'); await p.waitForSelector('#amt'); await p.click('[data-a=pay]'); await p.waitForSelector('[data-a=confirm]'); await p.click('[data-a=confirm]'); await p.waitForSelector('.rh'); await shot('branch-receipt-pending');
await fresh(); await p.selectOption('#out', '301'); await toEntry(); await fillStudent(); await p.click('[data-a=fetch]'); await p.waitForSelector('#amt'); await p.click('[data-a=pay]'); await p.waitForSelector('[data-a=confirm]'); await p.click('[data-a=confirm]'); await p.waitForSelector('.rh'); await shot('branch-receipt-failed');
console.log('shots', n, 'errors', errs); await b.close();
