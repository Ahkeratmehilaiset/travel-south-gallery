#!/usr/bin/env python3
"""Tarkistaa kaikki sivuston ulkoiset linkit (DOI ja URL) ja sisäiset linkit/ankkurit.
Luokat: OK (2xx/3xx), DEAD (404/410 tai nimipalvelu ei löydy), BLOCKED (401/403/429/5xx,
aikakatkaisu, robotinesto). Käyttö: python3 scripts/linkcheck.py [--internal-only]
"""
import os, re, sys, json, concurrent.futures as cf, urllib.request, urllib.error, socket, ssl
from html.parser import HTMLParser
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
class L(HTMLParser):
    def __init__(s): super().__init__(); s.links=[]; s.ids=set()
    def handle_starttag(s,t,a):
        a=dict(a)
        if a.get('id'): s.ids.add(a['id'])
        if t=='a' and a.get('href'): s.links.append(a['href'])
        if t in('img','link') and (a.get('src') or (t=='link' and a.get('rel')=='stylesheet' and a.get('href'))): s.links.append(a.get('src') or a.get('href'))
pages={}
for d,_,fs in os.walk(ROOT):
    if '/.git' in d or '/_tyo' in d or '/node_modules' in d: continue
    for f in fs:
        if f.endswith('.html'):
            p=os.path.join(d,f); x=L(); x.feed(open(p,encoding='utf-8').read()); pages[p]=x
ext={}; internal_bad=[]
for p,x in pages.items():
    for h in x.links:
        if h.startswith(('http://','https://')): ext.setdefault(h,set()).add(os.path.relpath(p,ROOT))
        elif h.startswith(('mailto:','data:','javascript:')): continue
        else:
            path,_,frag=h.partition('#')
            tgt=os.path.normpath(os.path.join(os.path.dirname(p),path)) if path else p
            if os.path.isdir(tgt): tgt=os.path.join(tgt,'index.html')
            if not os.path.exists(tgt): internal_bad.append((os.path.relpath(p,ROOT),h,'missing file')); continue
            if frag and tgt.endswith('.html'):
                t=pages.get(tgt)
                if t and frag not in t.ids: internal_bad.append((os.path.relpath(p,ROOT),h,'missing anchor'))
print(f'internal links checked; problems: {len(internal_bad)}')
for b in internal_bad[:50]: print('  INTERNAL',*b)
if '--internal-only' in sys.argv: sys.exit(1 if internal_bad else 0)
ctx=ssl.create_default_context()
def check(u):
    for method in ('HEAD','GET'):
        try:
            r=urllib.request.Request(u,method=method,headers={'User-Agent':UA,'Accept':'text/html,application/pdf,*/*','Accept-Language':'en,fi;q=0.8'})
            with urllib.request.urlopen(r,timeout=25,context=ctx) as resp: return ('OK',resp.status)
        except urllib.error.HTTPError as e:
            if method=='HEAD' and e.code in (403,405,400,404,429,500,501,503): continue
            if e.code in (404,410): return ('DEAD',e.code)
            return ('BLOCKED',e.code)
        except (urllib.error.URLError,socket.timeout,ConnectionError,ssl.SSLError) as e:
            reason=str(getattr(e,'reason',e))
            if 'Name or service not known' in reason or 'nodename nor servname' in reason or 'No address' in reason: return ('DEAD','DNS')
            if method=='HEAD': continue
            return ('BLOCKED',reason[:60])
        except Exception as e:
            if method=='HEAD': continue
            return ('BLOCKED',str(e)[:60])
    return ('BLOCKED','?')
res={}
with cf.ThreadPoolExecutor(16) as ex:
    for u,r in zip(ext, ex.map(check, list(ext))): res[u]=r
from collections import Counter
c=Counter(v[0] for v in res.values())
print('external unique URLs:',len(res),dict(c))
for u,(k,code) in sorted(res.items(),key=lambda x:x[1][0]):
    if k!='OK': print(f'  {k} {code} {u}  (e.g. {sorted(ext[u])[0]}, {len(ext[u])} pages)')
json.dump({u:list(v) for u,v in res.items()},open(os.path.join(ROOT,'..','ts-audit','linkcheck.json') if os.path.isdir(os.path.join(ROOT,'..','ts-audit')) else '/tmp/linkcheck.json','w'),indent=0)
sys.exit(0)
