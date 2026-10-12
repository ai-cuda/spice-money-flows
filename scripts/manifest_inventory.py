"""Phase 1: build a screen/entry-point inventory from a decoded AndroidManifest.xml.

Usage: python3 -I manifest_inventory.py <apktool_out_dir> <out_dir>
Writes activities.csv, deeplinks.csv, modules.csv, sdks.csv.
"""
import collections
import csv
import os
import sys
import xml.etree.ElementTree as ET

A = "{http://schemas.android.com/apk/res/android}"
APP_PREFIX = "spice.mudra."

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
root = ET.parse(os.path.join(src, "AndroidManifest.xml")).getroot()
pkg = root.get("package")
app = root.find("application")


def full(name):
    return pkg + name if name.startswith(".") else name


def module_of(name):
    if name.startswith(APP_PREFIX):
        rest = name[len(APP_PREFIX):].split(".")
        return rest[0] if len(rest) > 1 else "(root)"
    return None


def sdk_of(name):
    parts = name.split(".")
    return ".".join(parts[:3]) if len(parts) >= 3 else name


rows, links = [], []
for tag in ("activity", "activity-alias"):
    for el in app.findall(tag):
        name = full(el.get(A + "name"))
        target = full(el.get(A + "targetActivity") or "")
        flags = []
        for f in el.findall("intent-filter"):
            acts = {a.get(A + "name") for a in f.findall("action")}
            cats = {c.get(A + "name") for c in f.findall("category")}
            if "android.intent.category.LAUNCHER" in cats:
                flags.append("LAUNCHER")
            datas = f.findall("data")
            schemes = [d.get(A + "scheme") for d in datas if d.get(A + "scheme") is not None]
            hosts = [d.get(A + "host") for d in datas if d.get(A + "host")]
            paths = [d.get(A + "pathPrefix") or d.get(A + "path") or d.get(A + "pathPattern")
                     for d in datas if (d.get(A + "pathPrefix") or d.get(A + "path") or d.get(A + "pathPattern"))]
            if "android.intent.action.VIEW" in acts and schemes:
                flags.append("DEEPLINK")
                links.append({
                    "activity": name,
                    "schemes": " ".join(sorted(set(s for s in schemes if s))),
                    "hosts": " ".join(sorted(set(hosts))),
                    "paths": " ".join(sorted(set(paths))),
                    "browsable": "android.intent.category.BROWSABLE" in cats,
                })
        mod = module_of(target or name)
        rows.append({
            "activity": name,
            "kind": tag,
            "target": target,
            "owner": "app" if mod is not None else "sdk:" + sdk_of(name),
            "module": mod or "",
            "exported": el.get(A + "exported") or "",
            "entry_flags": " ".join(sorted(set(flags))),
            "screen_orientation": el.get(A + "screenOrientation") or "",
        })


def write(fn, data, fields):
    with open(os.path.join(out, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(data)


write("activities.csv", sorted(rows, key=lambda r: (r["owner"], r["module"], r["activity"])), list(rows[0]))
write("deeplinks.csv", links, ["activity", "schemes", "hosts", "paths", "browsable"])

mods = collections.Counter(r["module"] for r in rows if r["owner"] == "app")
write("modules.csv", [{"module": m, "activities": c} for m, c in mods.most_common()], ["module", "activities"])

sdks = collections.Counter(r["owner"][4:] for r in rows if r["owner"] != "app")
write("sdks.csv", [{"sdk_namespace": s, "activities": c} for s, c in sdks.most_common()], ["sdk_namespace", "activities"])

perms = sorted({p.get(A + "name") for p in root.findall("uses-permission")})
with open(os.path.join(out, "permissions.txt"), "w") as fh:
    fh.write("\n".join(perms) + "\n")

print(f"package={pkg} activities={len(rows)} app={sum(mods.values())} modules={len(mods)} "
      f"sdk_activities={sum(sdks.values())} deeplinks={len(links)} permissions={len(perms)}")
