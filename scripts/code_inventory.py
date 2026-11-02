"""Phase 1: scan decompiled app code (jadx output) for endpoints and layouts per module.

Usage: python3 -I code_inventory.py <jadx_sources_dir> <apktool_out_dir> <out_dir> [app_package] [api_host]
(app_package defaults to spice.mudra, api_host to spicemoney.com)
Writes endpoints.csv, layouts_by_module.csv, flutter_assets.csv and adds module stats to module_stats.csv.
"""
import collections
import csv
import os
import re
import sys

jadx_src, apk_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
app_root = os.path.join(jadx_src, *(sys.argv[4] if len(sys.argv) > 4 else "spice.mudra").split("."))

FULL_URL = re.compile(r"\"(https?://[a-z0-9.-]*" + re.escape(sys.argv[5] if len(sys.argv) > 5 else "spicemoney.com") + r"[^\"\s]*)\"")
CONCAT = re.compile(r'(\b[A-Za-z_][A-Za-z0-9_.]*(?:\(\))?)\s*\+\s*"([a-zA-Z0-9/_.\-]{3,}(?:\?[a-zA-Z0-9_=&\-]*)?)"')
RETRO = re.compile(r'@(GET|POST|PUT|DELETE|PATCH)\("([^"]*)"\)')
LAYOUT = re.compile(r'R\.layout\.([a-zA-Z0-9_]+)')
BASE_HINT = re.compile(r'(url|base|host|endpoint|api|constants)', re.I)


def module_of(path):
    rel = os.path.relpath(path, app_root).split(os.sep)
    return rel[0] if len(rel) > 1 else "(root)"


endpoints = {}
layouts = collections.defaultdict(set)
files_per_mod = collections.Counter()
for dirpath, _, files in os.walk(app_root):
    for fn in files:
        if not fn.endswith(".java"):
            continue
        p = os.path.join(dirpath, fn)
        mod = module_of(p)
        files_per_mod[mod] += 1
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        cls = os.path.relpath(p, jadx_src)[:-5].replace(os.sep, ".")
        for m in FULL_URL.finditer(text):
            endpoints.setdefault(("full", m.group(1)), set()).add((mod, cls))
        for m in CONCAT.finditer(text):
            base, path = m.group(1), m.group(2)
            # keep only things that look like API paths built on a URL-ish base
            if not BASE_HINT.search(base):
                continue
            if "." in path and "/" not in path:  # e.g. ".png", "file.txt"
                continue
            endpoints.setdefault(("concat", base.split(".")[-1] + " + " + path), set()).add((mod, cls))
        for m in RETRO.finditer(text):
            endpoints.setdefault(("retrofit", m.group(1) + " " + m.group(2)), set()).add((mod, cls))
        for m in LAYOUT.finditer(text):
            layouts[mod].add(m.group(1))

os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "endpoints.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["kind", "endpoint", "modules", "example_class"])
    for (kind, ep), uses in sorted(endpoints.items(), key=lambda kv: (sorted(kv[1])[0][0], kv[0][1])):
        mods = sorted({u[0] for u in uses})
        w.writerow([kind, ep, " ".join(mods), sorted(uses)[0][1]])

all_layouts = set()
res_layout = os.path.join(apk_dir, "res", "layout")
if os.path.isdir(res_layout):
    all_layouts = {f[:-4] for f in os.listdir(res_layout) if f.endswith(".xml")}
with open(os.path.join(out, "layouts_by_module.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["module", "layout"])
    for mod in sorted(layouts):
        for lay in sorted(layouts[mod]):
            w.writerow([mod, lay])

# Flutter assets (logic lives in libapp.so, absent from this base split)
fa = os.path.join(apk_dir, "assets", "flutter_assets", "assets")
fl = collections.Counter()
if os.path.isdir(fa):
    for dirpath, _, files in os.walk(fa):
        rel = os.path.relpath(dirpath, fa).split(os.sep)
        fl[rel[0] if rel[0] != "." else "(root)"] += len(files)
with open(os.path.join(out, "flutter_assets.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["flutter_asset_folder", "files"])
    for k, v in fl.most_common():
        w.writerow([k, v])

eps_per_mod = collections.Counter()
for uses in endpoints.values():
    for mod in {u[0] for u in uses}:
        eps_per_mod[mod] += 1
with open(os.path.join(out, "module_stats.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["module", "java_classes", "layouts_referenced", "endpoint_strings"])
    for mod, n in files_per_mod.most_common():
        w.writerow([mod, n, len(layouts.get(mod, ())), eps_per_mod.get(mod, 0)])

used = set().union(*layouts.values()) if layouts else set()
print(f"endpoints={len(endpoints)} modules={len(files_per_mod)} layouts_referenced={len(used)} "
      f"layouts_total={len(all_layouts)} flutter_asset_files={sum(fl.values())}")
