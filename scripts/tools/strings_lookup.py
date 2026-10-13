# Usage: python3 -I scripts/tools/strings_lookup.py <apktool_dir> <string_name>...  -> resolves strings.xml keys
import sys,re
A=sys.argv[1]
S=open(A+'/res/values/strings.xml',encoding='utf8').read()
d=dict(re.findall(r'<string name="([^"]+)"[^>]*>(.*?)</string>',S,re.S))
for k in sys.argv[2:]: print(k,'=>',d.get(k,'?')[:200])
