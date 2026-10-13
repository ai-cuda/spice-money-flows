#!/usr/bin/env bash
# Usage: scripts/tools/setup_decompile.sh <path/to/Spice_Money.apk> <work_dir>
# Downloads jadx 1.5.1 + apktool 2.10.0 (GitHub is on the workspace allowlist) and decompiles the APK.
# Output: <work_dir>/apktool (res, manifest, smali-free) and <work_dir>/jadx_full/sources (Java). Never commit these.
set -euo pipefail
APK="$1"; W="$2"; mkdir -p "$W/tools"; cd "$W/tools"
[ -f apktool.jar ] || curl -sSL -o apktool.jar https://github.com/iBotPeaches/Apktool/releases/download/v2.10.0/apktool_2.10.0.jar
[ -x jadx/bin/jadx ] || { curl -sSL -o jadx.zip https://github.com/skylot/jadx/releases/download/v1.5.1/jadx-1.5.1.zip && unzip -q -o jadx.zip -d jadx; }
cd "$W"
java -jar tools/apktool.jar d -f -s -o apktool "$APK" > apktool.log 2>&1
# Full decompile needs ~5 GB heap; the default heap runs out of memory on this APK.
JAVA_OPTS="-Xmx5g" tools/jadx/bin/jadx --show-bad-code -j 4 -d jadx_full "$APK" > jadx_full.log 2>&1 || true
echo "apktool: $W/apktool   jadx: $W/jadx_full/sources"
