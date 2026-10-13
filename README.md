# spice-money-flows

A screen-by-screen map of user flows in the Spice Money (adhikari) Android app, reconstructed from the APK.

**Repo policy:** analysis outputs and scripts only. The APK and the raw decompiled source are not committed; they can contain keys and are large.

## Phases

| Phase | Output | Status |
|---|---|---|
| 1. Static teardown | [INVENTORY.md](INVENTORY.md) and `inventory/` | Done (v6.6.62) |
| 2. Flow mapping from code | [flows/](flows/README.md): 10 journeys, plus clickable prototypes in `prototypes/`, with branches, conditions and findings | Done |
| 3. Screen rendering from layouts | `screens/rendered/` (169 screens) and the renderer in `scripts/render/` | Done |
| 4. Live capture on a device | [captures/live](captures/live/README.md): 25 live screens across 5 flows | Session 1 done; blocked by staging backends and test-ID permissions |
| 5. Packaging | Storyboard, deck or video per flow | |

## Regenerate the inventory

```bash
java -jar apktool.jar d -f -s -o out/apktool Spice_Money.apk
jadx -d out/jadx Spice_Money.apk
python3 -I scripts/manifest_inventory.py out/apktool inventory
python3 -I scripts/code_inventory.py out/jadx/sources out/apktool inventory
```
