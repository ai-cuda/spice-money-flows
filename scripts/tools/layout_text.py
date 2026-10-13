# Usage: python3 -I scripts/tools/layout_text.py <apktool_dir> <layout_name>...  -> every text/hint/title in a layout (resolved) + its includes
import sys,re,os
A=sys.argv[1]
S=open(A+'/res/values/strings.xml',encoding='utf8').read()
d=dict(re.findall(r'<string name="([^"]+)"[^>]*>(.*?)</string>',S,re.S))
for name in sys.argv[2:]:
    p=A+'/res/layout/'+name+'.xml'
    if not os.path.exists(p): print('##',name,'MISSING');continue
    t=open(p,encoding='utf8').read()
    out=[]
    for k,v in re.findall(r'(?:android|app):([a-zA-Z]*(?:[Tt]ext|[Hh]int|[Tt]itle|[Ll]abel))="([^"]*)"',t):
        if v.startswith('@string/'): v=v+' => '+d.get(v[8:],'?')
        if v and v not in out: out.append(v)
    inc=re.findall(r'layout="@layout/([^"]+)"',t)
    print('##',name,'| includes:',inc); [print('  ',o[:160]) for o in out]
