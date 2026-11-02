"""List every Retrofit endpoint in a jadx tree, including R8-obfuscated builds.

R8 renames Retrofit's annotations (@GET -> @ai3), so a plain "@GET(" grep finds
nothing in most release APKs. Retrofit's own request parser still names each verb
in a string ("GET", "POST", ...) next to an instanceof check on the renamed class,
so this script reads that mapping first, then scans interfaces for those annotations.

Usage: python3 -I retrofit_endpoints.py <jadx_sources_dir> [out.csv]
Prints a summary; writes verb,path,interface,method,file:line rows to out.csv.
Reads files only; never executes anything from the tree.
"""
import csv
import os
import re
import sys

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else None

VERBS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")
# instanceof X) { ... .b("VERB", ((X) a).value()   (obfuscated parser)
MAP_RE = re.compile(r'instanceof\s+([\w.$]+)\)\s*\{\s*[\w.$]+\.\w+\("(%s)",\s*\(\(\1\)' % "|".join(VERBS))
HTTP_GENERIC_RE = re.compile(r'instanceof\s+([\w.$]+)\)\s*\{\s*[\w.$]+\s+\w+\s*=\s*\(\1\)[^;]*;\s*[\w.$]+\.\w+\(\w+\.method\(\)')


def java_files(root):
    for d, dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".java"):
                yield os.path.join(d, f)


# Pass 1: annotation-class -> verb map. Real names first, then obfuscated ones.
amap = {v: v for v in VERBS}
amap.update({"retrofit2.http." + v: v for v in VERBS})
generic = {"HTTP", "retrofit2.http.HTTP"}
for p in java_files(src):
    try:
        t = open(p, encoding="utf-8", errors="ignore").read()
    except OSError:
        continue
    if '"GET"' not in t or "instanceof" not in t:
        continue
    for m in MAP_RE.finditer(t):
        cls = m.group(1).split(".")[-1]
        amap[cls] = m.group(2)
    for m in HTTP_GENERIC_RE.finditer(t):
        generic.add(m.group(1).split(".")[-1])

obf = {k: v for k, v in amap.items() if k not in VERBS and not k.startswith("retrofit2.")}

# Pass 2: annotated interface methods.
names = "|".join(re.escape(k.split(".")[-1]) for k in amap)
ANN_RE = re.compile(r'@(?:[\w.]+\.)?(%s)\(\s*(?:value\s*=\s*)?"([^"]*)"\s*\)' % names)
# @HTTP(method = "X", path = "/p", hasBody = true) with attributes in any order
GEN_RE = re.compile(r'@(?:[\w.]+\.)?(?:%s)\(([^)]*)\)' % "|".join(re.escape(g.split(".")[-1]) for g in generic))


def generic_hits(line):
    for m in GEN_RE.finditer(line):
        attrs = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1)))
        if "method" in attrs:
            yield attrs["method"].upper(), attrs.get("path", "")

rows = []
for p in java_files(src):
    try:
        lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
    except OSError:
        continue
    text = "\n".join(lines)
    if "interface " not in text:
        continue
    iface = re.search(r'interface\s+(\w+)', text)
    rel = os.path.relpath(p, src)
    for i, line in enumerate(lines):
        hits = [(amap[m.group(1)], m.group(2)) for m in ANN_RE.finditer(line)]
        hits += list(generic_hits(line))
        if not hits:
            continue
        # method name: first "name(" after stripping annotations from the next few lines
        tail = "\n".join(lines[i:i + 8])
        tail = re.sub(r'@[\w.$]+(?:\((?:[^()"]|"[^"]*")*\))?', " ", tail)
        mm = re.search(r'(\w+)\s*\(', tail)
        meth = mm.group(1) if mm else "?"
        for verb, path in hits:
            rows.append((verb, path, iface.group(1) if iface else "?", meth, "%s:%d" % (rel, i + 1)))

rows.sort(key=lambda r: (r[2], r[1], r[0]))
if out:
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["verb", "path", "interface", "method", "where"])
        w.writerows(rows)
print("obfuscated annotation map: %s" % (", ".join("%s=%s" % kv for kv in sorted(obf.items())) or "none (unobfuscated build)"))
print("endpoints=%d interfaces=%d" % (len(rows), len({r[2] for r in rows})))
for r in rows[:15]:
    print("  %-6s %-45s %s.%s  %s" % r)
if len(rows) > 15:
    print("  ... %d more%s" % (len(rows) - 15, " (see %s)" % out if out else ""))
