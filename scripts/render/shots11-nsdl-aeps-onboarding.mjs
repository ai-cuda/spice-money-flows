// Captures every screen of prototypes/aeps-nsdl-onboarding-prototype.html (phone frame only).
import { createRequire } from 'module';
import { execSync } from 'child_process';
const pw = createRequire(import.meta.url)(execSync('npm root -g').toString().trim() + '/playwright');
const OUT = process.env.OUT || new URL('../../captures/prototype/11-nsdl-aeps-onboarding/', import.meta.url).pathname;
const URL_ = new URL('../../prototypes/aeps-nsdl-onboarding-prototype.html', import.meta.url).href;
const b = await pw.chromium.launch(); const p = await b.newPage({ viewport: { width: 1380, height: 980 }, deviceScaleFactor: 2, locale: 'en-IN', timezoneId: 'Asia/Kolkata' });
const errs = []; p.on('pageerror', e => errs.push(e.message));
let n = 0; const shot = async (name, keep) => { n++; await p.waitForTimeout(260); if (!keep) await p.evaluate(() => document.querySelectorAll('.scr .toast').forEach(e => e.remove())); await p.locator('.phone').screenshot({ path: OUT + String(n).padStart(2, '0') + '-' + name + '.png' }); };
const lat = async v => { await p.fill('#lat', String(v)); await p.dispatchEvent('#lat', 'input'); };
const view = async y => { await p.locator('.scr .view').first().evaluate((e, y) => e.scrollTop = y, y); };
const until = sel => p.waitForSelector(sel, { timeout: 30000 });
const idle = () => p.waitForSelector('.loading', { state: 'detached', timeout: 30000 });
const fresh = async () => { await p.click('#reset'); await lat(150); };
const KO_AAD = '482739160521', STAFF_AAD = '735018622946', KO_AAD2 = '629184077358';
const typeOtp = async () => { await until('[data-otp]'); const sms = await p.textContent('#sms .m'); const otp = sms.match(/(\d{6}) is your OTP/)[1]; for (let i = 0; i < 6; i++) await p.fill(`[data-otp="${i}"]`, otp[i]); };
async function koDetailsDone() { await until('[data-a=kootp]'); await idle(); await p.click('[data-a=kootp]'); await typeOtp(); await p.click('[data-a=otpsubmit]'); await until('[data-a=kopan]:not([disabled])'); await idle(); await p.click('[data-a=kopan]'); await until('[data-a=koaddr]:not([disabled])'); await idle(); await p.click('[data-a=koaddr]'); await until('[data-a=ko2]:not([disabled])'); await idle(); }
async function koAadhaarDone() { await p.click('[data-a=ko2]'); await p.click('[data-a=doctype]'); await p.click('[data-a=pickdoc]'); await p.fill('#aad', KO_AAD); await p.check('#cons'); await p.click('[data-a=koscan]'); }
async function staffDetails() { await until('#sn'); await idle(); await p.fill('#sn', 'Sandeep Verma'); await p.fill('#sm', '7307815246'); await p.click('.uf [data-a=dob] >> nth=0'); await p.selectOption('#dd', '14'); await p.selectOption('#dm', '06'); await p.selectOption('#dy', '1998'); await p.click('[data-a=dobok]'); await p.fill('#se', 'sandeep.verma98@gmail.com'); await p.fill('#sp', 'BQTPV7712M'); }

await p.goto(URL_); await lat(150); await p.evaluate(() => document.fonts.ready);
// ===== KO via AePS mandate =====
await shot('home');
await lat(2500); await p.click('.tile.live'); await p.waitForTimeout(900); await shot('loading-do-ekyc'); await until('.hub button'); await shot('do-ekyc-list');
await until('[data-a=kootp]'); await p.waitForTimeout(700); await shot('nsdl-ekyc-loading-details'); await idle(); await lat(150); await shot('detail-verification');
await view(400); await shot('detail-verification-benefits'); await view(0);
await p.click('[data-a=help]'); await shot('helpline-numbers'); await p.click('.sheet [data-a=close]');
await p.click('[data-a=kootp]'); await typeOtp(); await shot('otp-sheet'); await p.click('[data-a=otpsubmit]'); await until('[data-a=kopan]:not([disabled])'); await idle(); await shot('mobile-verified');
await p.click('[data-a=kopan]'); await until('[data-a=koaddr]:not([disabled])'); await idle(); await shot('pan-verified');
await p.click('[data-a=koaddr]'); await until('[data-a=ko2]:not([disabled])'); await idle(); await shot('address-confirmed');
await p.click('[data-a=ko2]'); await shot('aadhaar-verification');
await p.fill('#aad', KO_AAD); await p.check('#cons'); await p.click('[data-a=koscan]'); await shot('scan-without-doc-type-does-nothing');
await p.click('[data-a=doctype]'); await shot('doc-type-picker'); await p.click('[data-a=pickdoc]');
await p.uncheck('#cons'); await p.click('[data-a=consent]'); await shot('aadhaar-consent'); await p.click('[data-a=consentok]'); await shot('consent-agreed-box-still-unticked');
await p.click('[data-a=koscan]'); await shot('consent-required-toast', 1);
await p.check('#cons'); await p.fill('#aad', '482739160522'); await p.click('[data-a=koscan]'); await shot('invalid-aadhaar-toast', 1);
await p.fill('#aad', KO_AAD); await shot('aadhaar-filled');
await p.click('[data-a=devices]'); await shot('select-biometric-device'); await p.click('[data-d=MANTRA_L1]');
await p.click('[data-a=koscan]'); await until('.cap'); await shot('fingerprint-capture');
await until('.kdone'); await shot('kyc-successfully-completed');
await until('.aepshead'); await shot('aeps-resumed', 1);
await p.click('[data-a=menu]'); await shot('aeps-menu');
await p.click('[data-a=managestaff]'); await until('[data-a=addstaff]'); await idle(); await shot('manage-staff-empty-list');
// ===== Sub-KO =====
await p.click('[data-a=addstaff]'); await until('#sn'); await idle(); await shot('add-sub-adhikari');
await p.click('[data-a=subpan]'); await shot('staff-name-required', 1);
await staffDetails(); await shot('staff-details-filled');
await p.click('.uf [data-a=dob] >> nth=0'); await shot('date-of-birth-picker'); await p.click('.cdlg [data-a=close]');
await p.click('[data-a=subpan]'); await until('.vok2'); await idle(); await shot('staff-pan-verified');
await p.click('[data-a=subotp]'); await shot('accept-terms-toast', 1);
await p.click('[data-a=tcd]'); await shot('terms-and-conditions'); await p.click('[data-a=tcok]');
await p.click('[data-a=subotp]'); await typeOtp(); await shot('staff-otp-sheet'); await p.click('[data-a=otpsubmit]');
await until('#aad'); await idle(); await shot('staff-aadhaar-verification');
await p.fill('#aad', STAFF_AAD); await p.click('[data-a=consent]'); await p.click('[data-a=consentok]'); await shot('staff-aadhaar-filled');
await p.click('[data-a=subscan]'); await until('#paad'); await idle(); await shot('adhikari-confirmation');
await p.fill('#paad', KO_AAD); await p.check('#pcons'); await p.click('[data-a=parentscan]'); await until('.cap'); await shot('adhikari-fingerprint-capture');
await until('.kdone'); await shot('sub-adhikari-kyc-done');
await until('.srow'); await idle(); await shot('manage-staff-one-staff');
await p.click('[data-a=viewstaff]'); await shot('sub-adhikari-details'); await p.click('.sheet [data-a=close]');
await p.click('[data-a=delstaff]'); await shot('delete-sub-adhikari');
await p.click('[data-a=delscan]'); await until('.cap'); await shot('delete-fingerprint-capture'); await until('[data-a=addstaff]'); await idle(); await shot('staff-deleted', 1);

// ===== Path B: Manage Staff first =====
await fresh(); await p.selectOption('#entry', 'staff'); await p.click('.tile.live'); await shot('b-aeps-without-mandate');
await p.click('[data-a=menu]'); await p.click('[data-a=managestaff]'); await until('[data-a=staffekyc]'); await idle(); await shot('b-manage-staff-do-ekyc-first');
await p.click('[data-a=staffekyc]'); await koDetailsDone(); await koAadhaarDone(); await until('[data-a=proceedonb]'); await shot('b-kyc-done-proceed-with-onboarding');
await p.click('[data-a=proceedonb]'); await shot('b-onboarded-successfully');
await p.click('[data-a=addlater]'); await until('[data-a=addstaff]'); await shot('b-add-later-manage-staff');
await p.selectOption('#entry', 'mandate');
// ===== branches =====
await fresh(); await p.selectOption('#staffN', '2'); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await koDetailsDone(); await koAadhaarDone(); await until('.aepshead'); await p.click('[data-a=menu]'); await p.click('[data-a=managestaff]'); await until('.srow'); await idle(); await shot('branch-two-staff'); await p.click('[data-a=addstaff]'); await shot('branch-staff-limit'); await p.selectOption('#staffN', '0');
await fresh(); await p.click('#popup'); await shot('branch-ekyc-popup-after-aeps');
await fresh(); await p.click('[data-a=account]'); await until('.hub button'); await idle(); await shot('branch-account-do-ekyc');
await fresh(); await p.selectOption('#init', 'resume'); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await shot('branch-resume-step-2'); await p.selectOption('#init', 'new');
await fresh(); await p.selectOption('#init', 'blocked'); await p.click('.tile.live'); await until('.dlg'); await shot('branch-init-blocked'); await p.selectOption('#init', 'new');
await fresh(); await p.selectOption('#otp', 'bad'); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await p.click('[data-a=kootp]'); await typeOtp(); await p.click('[data-a=otpsubmit]'); await p.waitForSelector('.toast'); await idle(); await shot('branch-invalid-otp', 1); await p.selectOption('#otp', 'ok');
await fresh(); await p.selectOption('#pan', 'bad'); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await p.click('[data-a=kootp]'); await typeOtp(); await p.click('[data-a=otpsubmit]'); await until('[data-a=kopan]:not([disabled])'); await idle(); await p.click('[data-a=kopan]'); await p.waitForSelector('.toast'); await idle(); await shot('branch-pan-mismatch', 1); await p.selectOption('#pan', 'ok');
await fresh(); await p.uncheck('#rd'); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await koDetailsDone(); await koAadhaarDone(); await until('.rdl'); await shot('branch-rd-service-not-installed'); await p.check('#rd');
await fresh(); await p.selectOption('#dev', 'nc'); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await koDetailsDone(); await koAadhaarDone(); await p.waitForSelector('.toast'); await shot('branch-device-not-connected', 1); await p.selectOption('#dev', 'ok');
await fresh(); await p.selectOption('#bio', 'bad'); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await koDetailsDone(); await koAadhaarDone(); await p.waitForSelector('.toast', { timeout: 30000 }); await idle(); await shot('branch-fingerprint-mismatch', 1); await p.selectOption('#bio', 'ok');
await fresh(); await p.click('.tile.live'); await until('[data-a=kootp]'); await idle(); await p.click('[data-a=ko1back]'); await shot('branch-back-opens-aeps-anyway', 1);
await fresh(); await p.uncheck('#tc'); await p.selectOption('#entry', 'staff'); await p.click('.tile.live'); await p.click('[data-a=menu]'); await p.click('[data-a=managestaff]'); await until('[data-a=staffekyc]'); await idle(); await p.click('[data-a=staffekyc]'); await koDetailsDone(); await koAadhaarDone(); await until('[data-a=proceedonb]'); await p.click('[data-a=proceedonb]'); await p.click('[data-a=addsub]'); await until('#sn'); await idle(); await view(400); await shot('branch-no-terms-text'); await p.check('#tc'); await p.selectOption('#entry', 'mandate');
await p.locator('.wrap').screenshot({ path: OUT + '00-workbench.png' });
console.log('shots', n, 'errors', JSON.stringify(errs)); await b.close();
