# 12 · Bill payment: Electricity (BBPS)

> **Confidence key:** ✅ confirmed in code · 🟡 inferred · ⬛ not visible in the APK (server data: billers, fields, amounts, campaigns)
>
> **Built from:** the APK (v6.6.62), the generic BBPS engine in [flow 05](05-bbps-bill-payment.md), and the electricity screens seen live on staging on 13 Oct ([captures/live/05](../captures/live/05/)).
>
> **Prototype:** [`prototypes/bbps-electricity-prototype.html`](../prototypes/bbps-electricity-prototype.html). Screenshots of every screen are in [`captures/prototype/12-electricity/`](../captures/prototype/12-electricity/).

## What is specific to electricity
- **Category identity:** `BBPSServiceEnum.ELECTRICITY`, category id **`7`** (the enum uses `Constants.CAMPAIGN_MAIN_CAMPAIGN = "7"`), text key `electricity`. ✅
- **Home tile:** "Electricity" in Recharges and Bills, in the first row on staging (13 Oct). Icon **`nd_tile_bbps_bulb`** via `KotlinCommonUtilityKt.q()`. ✅
- **Screens:** the same generic BBPS screens as every other category. There is no electricity-only screen. ✅
- **Billers and their fields:** server metadata ⬛. Real state boards each ask for their own identifier:
  - CA Number (BSES, Bihar);
  - Account Number (UP DISCOMs, PSPCL);
  - K Number (Rajasthan);
  - Consumer Number + Billing Unit (MSEDCL);
  - IVRS Number (MP);
  - Service Number (TN, AP, Torrent).

  The prototype uses these real board names and field labels. Bills and amounts are made up.
- **Location rule seen live:** Select State → Select Biller (state only, `cond1`). ✅ live
- **Campaign offer strip on the mobile-entry screen:** when `CAMPAIGN_FLAG = Y`, the category "Electricity" maps to the offer key `bbps_electricity_offer` (`BBPSMobileEntryActivity.onAddaPollItemClickListener`). ✅ code / ⬛ offer content. Not in the prototype.
- **Milestone cashback on the receipt** (for all BBPS billers, with electricity-specific campaign fields). ✅
  - **Shown when:** after a successful payment, if HomeINIT `bbpsCBMilestoneCommFlag = Y` and the biller `isBBPS = Y`.
  - **Call:** the app calls `https://bbps.spicemoney.com/commision-cashback/api/milestones` with `{categoryId, categoryName}`.
  - **On `responseCode 00` with milestones:**
    - the receipt shows the card **"Milestone based rewards"**, with **"Txn Count: {current}/{total}"**;
    - a horizontal row of milestones (target, cashback, achieved), and a tooltip from `message` (`"line1|line2"`);
    - the footer `mileStoneFooter`.
  - **Popup:** if `popupVisiblity.visible`, a full-screen dialog `dialog_milestone_archive` shows `"greeting|message"` and **OK**.
  - **Any other response:** a toast with `responseMessage`.
  - **Model:** `BbpsMilestoneCashbackResponse` also carries `electricitySpecialApplicable`. The commissions screen has `electricityText` / `electricityStructureList` for electricity-specific slabs. ⬛ campaign values.
  - **Older milestone call:** gated by `bbpsOfferMilesones = Y`: `bbpsservices…/fetchCashbackDetails/v1/fcd`.

  Evidence: `BBPSPaymentReceiptActivity` (~L545–592, `hitNewMilestoneCashback` ~L1112, response handling ~L2936, `showEarnedDialogNewCashback` ~L2121).

## Flow (generic engine, electricity values)
1. **Home:** Electricity tile.
2. **Mobile entry:** "Customer Mobile Number" and the upside-down CUSTOMER DISPLAY.
3. **Select State:** with "Use current location".
4. **Select Biller:** the state's boards (`fetchtopbillers`).
5. **Customer Details:** the board's field (CA / Account / K Number…). Then the note, Cash / UPI, and "Fetch bill details >".
6. **Fetch:** "Getting Bill, Please wait!" (`fetchbill/v1/fb` → `billresp/v1/pbr`).
7. **Bill detail:** Customer Name, Bill Number, Due Date, Bill Amount; View More (bill date, period, units, readings…); Amount within Minimum/Maximum Allowed; Total Payable; Pay.
8. **Confirm sheet:** `convfee/v1/cf`. Fee rows, View CCF Slab, Retailer Commission, Total customer pays, Confirm.
9. **Processing:** `paybill/v2/fpb`. A short wallet balance shows Low Wallet Balance (`P` + `SIB`).
10. **Receipt:** `billresp/v2/pbr` gives Successful / Pending / Failed, then the milestone card and the optional cashback popup.

## Observations
1. **The BBPS gate fires late** (seen live): "BBPS is currently unavailable in your log-in…" appears only after the adhikari has entered the mobile, picked a state and picked a board.
2. **No balance check before paying:** the low-balance message comes from the pay call (`SIB`). This is the same as every BBPS category.
3. **Milestone cashback is a strong retention hook on the most frequent BBPS category:** the receipt shows progress to the next cashback right after each bill. Its copy, targets and amounts are all server-driven ⬛.
4. **Staging data is messy:** a Jharkhand electricity biller appeared under Delhi (live, 13 Oct).

## What we could not see
- Real biller lists and field rules for each state, the bill fields each board returns, CCF and commission slabs, and campaign and milestone configuration (all server-side).
