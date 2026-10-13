# Phase 2: user flows mapped from code

The seven priority journeys in Spice Money v6.6.62, traced screen by screen from the decompiled APK. Each file follows [`_TEMPLATE.md`](_TEMPLATE.md): a summary, a Mermaid diagram, a screen table with real on-screen text and API calls, branches, gaps, a phase 4 checklist and code evidence.

**Confidence:** ✅ confirmed in code · 🟡 inferred · ⬛ not visible in the APK (backend, Flutter, partner SDK)

| # | Flow | Entry point | Rows | ✅ / 🟡 / ⬛ |
|---|---|---|---|---|
| 01 | [Login & first launch](01-login-first-launch.md) | Launcher → `SplashActivity` | 18 | 34 / 11 / 11 |
| 02 | [New adhikari onboarding (aob7)](02-adhikari-onboarding.md) | "Create account" on Login, Singular links | 23 | 62 / 8 / 13 |
| 03 | [AePS cash withdrawal](03-aeps-cash-withdrawal.md) | Tile `AEPS_CW` | 23 | 62 / 23 / 12 |
| 04 | [Money transfer (DMT)](04-dmt-money-transfer.md) | Tile `DMT_ONE_BC` | 24 | 57 / 17 / 4 |
| 05 | [Bill payment (BBPS) + recharge](05-bbps-bill-payment.md) | Category grid / any tile with service details `B|…` | 22 | 61 / 8 / 7 |
| 06 | [Wallet add money & Spice Pay](06-wallet-add-money-spicepay.md) | Tiles `ADD_MONEY`, `REQUEST_FUNDS`, `SP_QRCD`/`SP_QRCW` | 23 | 42 / 17 / 11 |
| 07 | [UPI Cash Point](07-upi-cash-withdrawal.md) | Tile `UpiCWFlagnewweb`, deep link `upicashwithdrawal` | 19 | 48 / 11 / 6 |
| 08 | [Axis savings Re-KYC](08-axis-rekyc.md) | Tile `axis_rekyc` | 13 | storyboard in `storyboards/axis-rekyc.html` |
| 09 | [Bill payment: Education Fees](09-bbps-education-fees.md) | Recharges and Bills → View More → Education Fees (category 27) | 10 | prototype in `prototypes/bbps-education-fees-prototype.html` |

## How the app is put together (common to all flows)

- **Server-driven everywhere.** Home tiles come from `init/v2`. Feature flags choose between old and new versions of most journeys: `newaepsrevamp`, `newwalletrevamp`, `DMT2`/`ASSIST_DMT`, `insourcing_spob`. Biller metadata drives the BBPS forms. Payment modes in add-money come from the server.
- **Old versions still ship.** There are three add-money interfaces, two AePS screens, two UPI cash-withdrawal products, and onboarding versions aob4 to aob7. Several old screens can no longer be reached.
- **The gates before a transaction repeat across flows:** eKYC mandate (YBL/NSDL/RBL), daily agent 2FA, location, onboarding transaction threshold, service packs and risk blocks.
- **Cross-sell is built into the success screens.** AePS success screens promote UPI Cash Point and Spice Pay onboarding. The deposit form promotes Working Capital credit.

## Findings worth a product discussion

These are confirmed in code unless marked 🟡. Each one is a hypothesis to validate in live capture, not a verdict.

1. **AePS: pending withdrawals look like failures.** A pending (`UNK`) withdrawal shows the same red "Transaction Failed / Retry Again" popup as a real failure, and nothing checks the status afterwards. That invites retries and possible double payouts. *(Spot-checked: `NewAepsRevampFragment.showBalDialog`.)*
2. **BBPS: no balance check before paying.** The pay call itself fails with `SIB`, and only then does the app show "Add ₹X balance". Bill fetch and the receipt can each poll for up to about a minute. *(Spot-checked.)*
3. **Wallet top-up by UPI trusts the customer's UPI app.** The result screen relies on what the UPI app reports back, with no server status check, unlike the legacy flow. Paying by scanning from another phone gives no callback at all. 🟡 where the classes did not decompile.
4. **UPI Cash Point has no closing step and no cancel.** There is no "cash handed over" confirmation and no customer OTP. Backing out of a live QR calls no cancel API.
5. **DMT asks for the pattern after the OTP.** The agent's pattern is checked after the customer's OTP is spent, so a failed pattern may leave an authorised transfer that was never sent 🟡. A pending split transfer shows UPI wording.
6. **First launch:** Hindi devices are switched back to English, the permissions screen doesn't actually request any permissions, there is no PIN check when the app is reopened, and login is blocked when no location fix is available.
7. **Onboarding:** marketing-link users are sent to the old aob5 dashboard, and eSign and video KYC are not part of signup in this build.
8. **Dead code:** AePS-funded bill pay, the Academy certification gate, service-based BBPS complaints, old recharge screens and the refund screens.

## Known limits of this pass

- The first full decompile ran out of memory, so the mappers decompiled missing classes one at a time. Those citations point to the scratchpad and not to the main source tree. A full re-decompile with more memory is in progress for phase 3.
- Flutter code (wallet, insurance, inventory, market toolkit) is not in this base APK.
- All limits, fees, risk rules and reconciliation happen on the server.
