# Phase 1: Spice Money app inventory

**Source:** `Spice_Money.apk`, package `in.spicemudra`, version **6.6.62** (code 502), target SDK 36.
**Method:** static teardown with jadx 1.5.1 and apktool 2.10.0. The app was not run.

## Headline numbers

| What | Count | Notes |
|---|---|---|
| Screens (activities) declared | **694** | 641 are Spice Money's own; 53 come from SDKs |
| App feature packages (`spice.mudra.*`) | 132 | 78 of them declare screens |
| Java classes in app code | ~6,050 | Class names are readable; light obfuscation only |
| Screen layouts (XML) | 2,332 | 752 are referenced directly by code; the rest are loaded through view binding |
| Backend endpoint strings found | 241 | 154 full URLs, 75 base+path pairs, 12 Retrofit routes |
| Backend hosts (`*.spicemoney.com`) | 25+ | e.g. api-gw, app, aepsapp, dmt, nsdlcasa, myapp, insurance |
| Flutter asset files | 1,266 | The Flutter screens' logic is **not** in this APK (see limits) |
| Permissions | 51 | |

## Entry points

- **Launcher:** `SplashActivity`. It routes to `DashboardActivityRevamp` (home), `WelcomeActivity`, `RequiredPermissionActivity` or a web view.
- **Login:** `LoginActivity`. It routes to:
  - home,
  - intro (`SpiceMoneyIntro`),
  - `ForgotPin` / `ForgotPassword`,
  - `SetPattern`,
  - onboarding status (`AOBCurrentstatusActivity`),
  - SIM-binding (`SimNumberSelectionActivityAob7`).
- **Home-tile router:** `newDashboard/utility/serviceHandling/ServiceActionHandler` and `RedirectionHandler`, with specialised redirectors for Axis, NSDL, Insurance, Loans and web content. About 30 branches and 53 service codes. **This is the backbone for mapping flows in phase 2.**
- **Deep links:** all of them land on `SplashActivity`:
  - `spiceapp://`
  - `spicenudges://`
  - `spiceapplink.sng.link/{A,B,E,F}` (Singular attribution links)
  - `vf.spicemoney.com/product/…`

## Feature map (grouped from package names; to be confirmed in phase 2)

| Domain | Packages (screens) | Size signal |
|---|---|---|
| **App shell, login & home** | `activity` (113, mixed), `newDashboard` (9), `dynamicDash`, `mpin` (5), `forgotId`, `resetPassword`, `intro`, `welcomeKit`, `notifactionrevamp`, `settingtds_more`, `coachmarks` | `newDashboard` holds 27 endpoint strings |
| **Agent onboarding & KYC** | `aob7` (10), `aob5` (5), `aob_lite_onboarding` (6), `aob_FSE_onboarding` (7), `aob_for_distributor` (12), `firstLoginAob`, `ekycsdk` (6), `rekyc2_0`, `nsdlekyc`, `nsdl_ybl_rekyc`, `yblekyc`, `rblekyc`, `csp_profilling`, `csplocationcapture` (5), `esignmodule` (5), video-KYC screens; HyperVerge SDK | Several generations of onboarding (aob4 → aob7, lite, FSE) |
| **Cash-out: AePS, mATM, Aadhaar Pay, UPI cash** | `aeps` (24), `aadhaarpay` (7), `matm`, `matmrewamp`, `matm_newdevice`, `mosambee`, `fingpay`, biometric device drivers (`mantra_module`, `morphomodule`, `precision`), `upiwithdraw` (10), `merchant_cash` (6), `devicerepair` | Biometric devices and printers are integrated |
| **Money transfer (DMT)** | `dmt2_0` (15), `dmtassistant` (9), `onebcdmt`, `onebc`, `accessdmtonweb` | |
| **Bank accounts as a banking correspondent** | `nsdl` (96 screens, the biggest by screen count), `axis` (51), `csp_cred` (19), `newbank` | NSDL and Axis account opening/servicing |
| **Bill pay & recharge** | `bbps` (40 screens, 638 classes, the biggest by code), tariff plans, IRCTC | |
| **Wallet, PPI & Spice Pay** | `walletRevamp` (18), `wallethistorynew` (14), `full_ppi_account` (18), `spicepay`, `spicepayqrscan` (7), `upipos` (7), `addMoneyNew`, UPI screens in `activity` | Links to your PPI wallet workstream |
| **Credit, insurance & gold** | `happyLoans` (5), `loancredit`, `workingcapital`, `grahakApp`, `vbd` (insurance), Jar gold SDK, `Gold*` models, `creditcardpayment`, `dehaat` | Mostly web views to partner sites |
| **Growth & engagement** | `prachaar_3_0` (marketing toolkit), `vip` (8), `milestones`, `campaign`, `servicepacks`, `prefferedplan`, `miniplans`, `addtools`, `academy`/`training`, `videoAvatar`, `voicefeatures`, `chatbot_Spice`, `botsupport`, `movetodistributor`, earnings and invite screens | |
| **Risk & operations** | `fraudmonitoring`, `integrity`, `outage`, `LockDown`, heartbeat and device-support services | |

**Flutter modules** (identified from asset folders only): wallet, insurance, inventory, market toolkit, change password, plus shared images and Lottie loaders.

**Third-party screens:**
- KYC: HyperVerge (13), NSDL e-Gov (9), FinoPay (6), Religare PAN, FRS Labs
- Payments: Mosambee (mATM)
- Engagement: Netcore (CRM), Jar (gold), plus a Flutter in-app web view

## Files

| File | What it holds |
|---|---|
| `inventory/activities.csv` | Every screen: owner, module, whether it is exported, entry flags |
| `inventory/modules.csv`, `inventory/module_stats.csv` | Screens, classes, layouts and endpoints per module |
| `inventory/deeplinks.csv` | Deep-link schemes and hosts |
| `inventory/endpoints.csv` | Backend URLs and paths, with the module and class that use each one |
| `inventory/layouts_by_module.csv` | Which layouts each module's code references |
| `inventory/sdks.csv`, `inventory/permissions.txt`, `inventory/flutter_assets.csv` | SDK screens, permissions, Flutter asset folders |
| `scripts/` | Scripts that regenerate all of the above from a new APK |

## Known limits

1. **This is the base split only.** The manifest requires `abi` and `density` splits, and there are no native libraries. So the Flutter code (`libapp.so`) is missing and the APK will not install by itself.
2. **Endpoints are partial.** Many request URLs are assembled at runtime from a constant plus a variable, so the list is a floor, not a full catalogue.
3. **Server-side logic is invisible.** Eligibility, limits and feature flags decided by the backend only show up as the app's handling of the responses.
4. **About two-thirds of layouts are reached through view binding,** so the layout-to-screen mapping will be completed in phase 2.
