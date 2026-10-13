// Captures every screen of prototypes/bbps-loan-repayment-prototype.html (phone frame only).
import { createRequire } from 'module';
import { execSync } from 'child_process';
const pw = createRequire(import.meta.url)(execSync('npm root -g').toString().trim() + '/playwright');
const OUT = new URL('../../captures/prototype/10-loan-repayment/', import.meta.url).pathname;
const URL_ = new URL('../../prototypes/bbps-loan-repayment-prototype.html', import.meta.url).href;
const b = await pw.chromium.launch(); const p = await b.newPage({ viewport: { width: 1380, height: 980 }, deviceScaleFactor: 2, locale: 'en-IN', timezoneId: 'Asia/Kolkata' });
const errs = []; p.on('pageerror', e => errs.push(e.message));
let n = 0; const shot = async (name, keep) => { n++; await p.waitForTimeout(260); if (!keep) await p.evaluate(() => document.querySelectorAll('.scr .toast, .scr .notif').forEach(e => e.remove())); await p.locator('.phone').screenshot({ path: OUT + String(n).padStart(2, '0') + '-' + name + '.png' }); };
const lat = async v => { await p.fill('#lat', String(v)); await p.dispatchEvent('#lat', 'input'); };
const view = async y => { await p.locator('.scr .view').first().evaluate((e, y) => e.scrollTop = y, y); };
const sheet = async y => { await p.locator('.scr .sheet').first().evaluate((e, y) => e.scrollTop = y, y); };
const slow = async (click, name, waitSel) => { await lat(2500); await p.click(click); await p.waitForTimeout(600); await shot(name); if (waitSel) await p.waitForSelector(waitSel, { timeout: 30000 }); await lat(150); };
const fresh = async () => { await p.click('#reset'); await lat(150); };
const MOB = '9839214670';
const until = async sel => p.waitForSelector(sel, { timeout: 30000 });
async function toEntry(lender = 0) { await p.click('.tile.live'); await p.fill('#mob', MOB); await p.click('[data-a=cont]'); await until('[data-a=biller]'); await p.click(`[data-a=biller] >> nth=${lender}`); }
async function fillSingle() { await p.fill('#p0', 'SMF0014521876'); if (await p.$('#rem')) await p.fill('#rem', 'Ramesh Kumar'); }
async function payToReceipt() { await p.click('[data-a=fetch]'); await until('.emi, #amt'); if (await p.$('.emi')) await p.click('.emi >> nth=0'); await p.click('[data-a=pay]'); await until('[data-a=confirm]'); await p.click('[data-a=confirm]'); }
async function toCustomers() { await p.click('[data-a=tabbulk]'); await p.click('[data-a=photo]'); await p.click('[data-a=opencam]'); await p.click('[data-a=shutter]'); await p.click('[data-a=cropok]'); }
async function addMobiles() { await p.click('[data-a=addmissing]'); const ins = await p.$$('[data-mi]'); const M = ['9839214670', '9721038845', '8840172593', '9452260718', '7307815246', '9118342067']; for (let i = 0; i < ins.length; i++) await ins[i].fill(M[i]); }

await p.goto(URL_); await lat(150); await p.evaluate(() => document.fonts.ready);
// ===== single repayment =====
await shot('home');
await view(520); await shot('home-recharges-and-bills-loan-tile');
await p.click('.tile.live'); await shot('mobile-entry');
await p.fill('#mob', MOB); await shot('mobile-entry-customer-display');
await slow('[data-a=cont]', 'loading-lenders', '[data-a=biller]');
await shot('select-lender');
await p.click('[data-a=biller] >> nth=0'); await shot('loan-details-single-repayment');
await p.fill('#p0', 'SMF0014521876'); await p.fill('#rem', 'xqzt'); await p.click('[data-a=fetch]'); await shot('remitter-name-invalid', 1);
await p.fill('#rem', 'Ramesh Kumar'); await shot('loan-details-filled');
await slow('[data-a=fetch]', 'fetching-dues', '.emi');
await shot('emi-two-loans-found');
await p.click('[data-a=pay]'); await shot('emi-select-bill-toast', 1);
await p.click('.emi >> nth=0'); await shot('emi-selected');
await p.click('details summary'); await view(400); await shot('emi-view-more');
await p.click('[data-a=pay]'); await until('[data-a=confirm]'); await shot('confirm-payment');
await p.click('[data-a=slab]'); await shot('ccf-slab');
await p.click('[data-a=backconfirm]');
await slow('[data-a=confirm]', 'processing-payment');
await until('.rh'); await shot('receipt-success');
await view(600); await shot('receipt-success-share');
await p.click('.copy'); await shot('receipt-loan-number-copied', 1);

// ===== bulk repayment: photo path =====
await fresh(); await toEntry(); await p.click('[data-a=tabbulk]'); await shot('bulk-upload-options');
await p.click('[data-a=howto]'); await shot('bulk-how-to-use'); await p.click('[data-a=close]');
await p.click('[data-a=photo]'); await shot('bulk-scan-document-sheet');
await p.click('[data-a=opencam]'); await shot('bulk-camera');
await p.click('[data-a=shutter]'); await shot('bulk-crop-document');
await lat(2500); await p.click('[data-a=cropok]'); await p.waitForTimeout(900); await shot('bulk-scanning-document');
await p.click('[data-a=exitscan]'); await shot('bulk-exit-scanning-dialog'); await p.click('.dlg [data-a=close]');
await until('.ccard'); await lat(150); await shot('bulk-customers-found');
await view(700); await shot('bulk-customers-list');
await view(0); await p.click('[data-a=getbills]'); await shot('bulk-customers-missing-mobile', 1);
await addMobiles(); await shot('bulk-add-mobile-number'); await p.click('[data-a=missadd]');
await p.click('[data-a=prefix]'); await p.fill('#pfx', 'SMF'); await p.check('#pfxok'); await shot('bulk-add-prefix'); await p.click('[data-a=pfxsave]');
await shot('bulk-customers-ready');
await p.click('[data-a=addcust]'); await shot('bulk-add-customer-sheet'); await p.click('.sheet [data-a=close]');
await p.click('[data-a=delcust] >> nth=2'); await shot('bulk-delete-customer-dialog'); await p.click('.dlg [data-a=close]');
await lat(2500); await p.click('[data-a=getbills]'); await p.waitForTimeout(3000); await shot('bulk-fetching-bills-progress');
await p.waitForSelector('.loading >> text=Checking Mismatches', { timeout: 30000 }); await p.waitForTimeout(300); await shot('bulk-checking-mismatches');
await until('[data-a=mmreview]'); await lat(150); await shot('bulk-data-mismatch-warning');
await p.click('.sheet [data-a=mmreview]'); await shot('bulk-mismatch-review');
await p.click('[data-a=mmaccept] >> nth=0'); await shot('bulk-mismatch-one-resolved');
await p.click('[data-a=mmaccept] >> nth=0'); await shot('bulk-bill-details', 1);
await view(800); await shot('bulk-bill-details-totals');
await view(0); await p.click('[data-a=editamt] >> nth=0'); await shot('bulk-edit-amount'); await p.click('.dlg [data-a=close]');
await p.check('#ccfall'); await p.click('[data-a=bconfirm]'); await shot('bulk-payment-review');
await p.click('[data-a=decl]'); await shot('bulk-declaration'); await p.click('.sheet [data-a=close]');
await p.check('#decl'); await view(900); await shot('bulk-declaration-accepted');
await p.selectOption('#bout', 'fail3');
await p.click('#proceed'); await until('[data-a=paynow]:not([disabled])'); await p.waitForSelector('.loading', { state: 'detached' }); await shot('bulk-pay-bill-1-of-6');
await p.click('[data-a=slabs]'); await shot('bulk-commission-slabs'); await p.click('.dlg [data-a=close]');
await slow('[data-a=paynow]', 'bulk-processing-bill-1');
await p.waitForSelector('.toast'); await p.waitForSelector('.loading', { state: 'detached' }); await shot('bulk-bill-1-paid-next-bill-2', 1);
const payOne = async () => { await p.click('[data-a=paynow]'); await p.waitForFunction(() => document.querySelector('.toast')); await p.waitForSelector('.loading', { state: 'detached', timeout: 30000 }); };
await payOne(); await p.click('[data-a=paystatus]'); await shot('bulk-payment-status-sheet'); await p.click('.sheet [data-a=close]');
await payOne(); await shot('bulk-bill-3-failed-toast', 1);
await p.click('[data-a=exitpay]'); await shot('bulk-exit-dialog'); await p.click('.dlg [data-a=close]');
await p.click('[data-a=skip]'); await p.waitForSelector('.toast >> text=Bill skipped.'); await p.waitForSelector('.loading', { state: 'detached' }); await shot('bulk-bill-4-skipped', 1);
await payOne(); await payOne(); await until('.tabs'); await shot('bulk-payment-summary');
await p.click('[data-a=stab][data-t=Failed]'); await shot('bulk-summary-failed-tab');
await p.click('[data-a=stab][data-t=Skipped]'); await shot('bulk-summary-skipped-tab');
await p.click('[data-a=stab][data-t=Success]'); await shot('bulk-summary-success-tab');
await p.click('.trow >> nth=0'); await shot('bulk-transaction-details'); await sheet(600); await shot('bulk-transaction-details-more'); await p.click('.sheet [data-a=close]');
await p.click('[data-a=dlall]'); await p.waitForSelector('.notif'); await shot('bulk-download-all-receipts', 1);
await p.selectOption('#bout', 'ok');

// ===== bulk branches =====
await fresh(); await p.selectOption('#scan', '01'); await toEntry(); await toCustomers(); await until('[data-map]'); await shot('bulk-import-data-needs-mapping');
await p.selectOption('[data-map="Loan Account Number"]', 'Loan No'); await shot('bulk-import-data-mapped'); await p.click('[data-a=mapcont]'); await until('.ccard'); await shot('bulk-customers-after-mapping');
await fresh(); await p.selectOption('#scan', '02'); await toEntry(); await toCustomers(); await until('.dlg'); await shot('bulk-could-not-read-document'); await p.selectOption('#scan', '00');
await fresh(); await toEntry(); await p.click('[data-a=tabbulk]'); await p.click('[data-a=dlsample]'); await until('.notif'); await shot('bulk-download-format-notification', 1);
await p.click('[data-a=excel]'); await shot('bulk-excel-document-upload'); await p.click('[data-a=pickfile]'); await shot('bulk-excel-file-picker');
await p.click('[data-f="Kendra14_EMI_Oct2026.xlsx"]'); await shot('bulk-excel-file-selected');
await lat(2500); await p.click('[data-a=extract]'); await p.waitForTimeout(900); await shot('bulk-excel-fetching-details'); await until('.ccard'); await lat(150); await shot('bulk-excel-customers');
await fresh(); await p.selectOption('#bal', '6500'); await p.uncheck('#mm'); await toEntry(); await toCustomers(); await until('.ccard'); await addMobiles(); await p.click('[data-a=missadd]'); await p.click('[data-a=prefix]'); await p.fill('#pfx', 'SMF'); await p.check('#pfxok'); await p.click('[data-a=pfxsave]'); await p.click('[data-a=getbills]'); await until('.bcard'); await p.waitForSelector('.loading', { state: 'detached' }); await view(900); await shot('bulk-low-wallet-balance'); await p.selectOption('#bal', '52000'); await p.check('#mm');
await fresh(); await toEntry(); await toCustomers(); await until('.ccard'); await addMobiles(); await p.click('[data-a=missadd]'); await p.click('[data-a=getbills]'); await until('.dlg'); await shot('bulk-no-prefix-no-bills-found');
await fresh(); await p.selectOption('#meth', 'EXCEL'); await toEntry(); await p.click('[data-a=tabbulk]'); await p.click('[data-a=excel]'); await shot('bulk-excel-only-card-does-nothing'); await p.selectOption('#meth', 'both');
await fresh(); await p.selectOption('#bulk', 'off'); await toEntry(); await shot('bulk-switched-off-no-toggle'); await p.selectOption('#bulk', 'on');
// ===== single branches =====
await fresh(); await p.uncheck('#enabled'); await p.click('.tile.live'); await shot('branch-bbps-not-enabled'); await p.check('#enabled');
await fresh(); await p.selectOption('#crit', 'cond1'); await p.click('.tile.live'); await p.fill('#mob', MOB); await p.click('[data-a=cont]'); await shot('branch-select-state'); await p.click('[data-a=pick] >> text="Uttar Pradesh"'); await until('[data-a=biller]'); await shot('branch-lenders-in-uttar-pradesh'); await p.selectOption('#crit', 'all');
await fresh(); await p.selectOption('#emi', 'none'); await toEntry(); await fillSingle(); await p.click('[data-a=fetch]'); await until('.dlg'); await shot('branch-nothing-due'); await p.selectOption('#emi', 'multi');
await fresh(); await p.selectOption('#emi', 'one'); await toEntry(3); await p.fill('#p0', 'KMTW2024UP118734'); await p.fill('#rem', 'Ramesh Kumar'); await p.click('[data-a=fetch]'); await until('#amt'); await shot('branch-one-emi-due'); await p.selectOption('#emi', 'multi');
await fresh(); await p.uncheck('#remit'); await toEntry(); await shot('branch-no-remitter-field'); await p.check('#remit');
await fresh(); await p.selectOption('#bal', '6500'); await p.selectOption('#emi', 'one'); await toEntry(4); await p.fill('#p0', 'GHFL0098211450'); await p.fill('#rem', 'Ramesh Kumar'); await p.click('[data-a=fetch]'); await until('#amt'); await p.click('[data-a=pay]'); await until('[data-a=confirm]'); await p.click('[data-a=confirm]'); await until('[data-a=addbal]'); await shot('branch-low-wallet-balance'); await p.selectOption('#bal', '52000'); await p.selectOption('#emi', 'multi');
await fresh(); await lat(1500); await toEntry(); await fillSingle(); await p.check('input[name=pm][value=UPI]'); await payToReceipt(); await until('.qr'); await shot('branch-upi-customer-qr'); await lat(150);
await fresh(); await p.selectOption('#out', '001'); await toEntry(); await fillSingle(); await payToReceipt(); await until('.rh'); await shot('branch-receipt-pending');
await fresh(); await p.selectOption('#out', '301'); await toEntry(); await fillSingle(); await payToReceipt(); await until('.rh'); await shot('branch-receipt-failed'); await p.selectOption('#out', '000');
await fresh(); await p.selectOption('#loanRow', 'hide'); await toEntry(); await fillSingle(); await payToReceipt(); await until('.rh'); await shot('branch-receipt-loan-number-hidden'); await p.selectOption('#loanRow', 'show');
await p.locator('.wrap').screenshot({ path: OUT + '00-workbench.png' });
console.log('shots', n, 'errors', JSON.stringify(errs)); await b.close();
