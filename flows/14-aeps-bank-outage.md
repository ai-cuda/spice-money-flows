# 14 · AePS: selected bank is in outage

> **Confidence key:** ✅ confirmed in code · 🟡 inferred · ⬛ not visible in APK (backend)

## Summary
When the server flag `apes_oyateg_flag^$^^&%&%` (AEPS_OUTAGE_FLAG) is `Y`, every bank the adhikari picks on the AePS screen is checked with `POST {CORE_URL_AEPS_INIT}outage/info/app` before it is selected. If the response is not `responseStatus=S`, the app shows the `rekyc_dialog` layout as a non-cancellable popup:

- Icon: `@drawable/exclamation_triangle`
- Title: `bankName + " is facing issues"` (hard-coded)
- Body: `responseMessage` from the server ⬛
- Button: **Try Later**: closes the popup; the bank is not selected
- Link: **Continue Anyway**: selects the bank anyway

The same popup exists in two places ✅:
- `NewAepsRevampFragment.showOutageDialog`: tapping one of the 5 quick-pick banks (`addBankListAdapter$lambda$0`) or a bank from the Aadhaar Pay/AePS QR scan.
- `AEPSBankSelectionActivity.showOutageDialog`: "View All" → *Select Customer’s Bank* (tabs "All banks" / "Favourite banks").

## Branches
- Flag off → no API call; the bank is selected directly ✅
- `responseStatus=S` → bank selected (`selectBankById` / `setResult`) ✅
- Any other status → outage popup; analytics `Bank outage- {message}`; SpiceBot error code `AEPS_BANK_OUTAGE` ✅
- Null response → MaterialDialog "Error" / "Something went wrong. Please try again." / OK ✅
- `Status.ERROR` → `CommonUtility.handleError` (server errorMsg / respDesc) ✅

## Request / response
- Request body: `iin`, `transType` (service), `token`, `bcAgentId`, `appVersion` (encoded); headers token, mode=APP, bcAgentId, clientId ✅
- Response model `AepsOutageBankResponse`: `responseStatus`, `responseMessage`, `responseCode`, `messsage`, `fs`. The app reads only `responseStatus` and `responseMessage` ✅

## Product observations
1. **The outage message is entirely server-written.** The app adds only the title, so the copy quality depends on whoever sets it in the backend.
2. **"Continue Anyway" lets the transaction go ahead** against a bank that the server says is down. A likely failure, and a fingerprint and a customer's time spent.
3. **The check runs at bank pick only.** It doesn't run again at "Scan finger", so an outage that starts after the bank is picked is not caught here.
4. **The primary button is "Try Later",** but "Try Later" only closes the popup. The adhikari is left on the same screen with no bank selected and no suggestion of an alternative.

## Prototype
`prototypes/aeps-bank-outage-prototype.html`. 16 screenshots in `captures/prototype/14-aeps-bank-outage/`, script `scripts/render/shots14-aeps-bank-outage.mjs`. The bank IINs and the outage message are invented.
