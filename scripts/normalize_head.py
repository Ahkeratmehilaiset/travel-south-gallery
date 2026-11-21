#!/usr/bin/env python3
"""Yhtenäistää kaikkien kielisivujen head-osan ja kielivalikot:
absoluuttiset hreflang-linkit + x-default, oma canonical, og:url, og:locale,
kielivalikko (aria-current="page"), aloitussivun hub-langs, yksi GoatCounter-tagi,
merkintä- ja kuvatekstielementtien erotus, sitemap.xml. Aja reposta: python3 scripts/normalize_head.py
"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://ahkeratmehilaiset.github.io/travel-south-gallery/'
LANGS = ['en','fi','sv','de','fr','es','it','ru','uk','ja','ar','zh']
NAMES = {'en':'English','fi':'Suomi','sv':'Svenska','de':'Deutsch','fr':'Français','es':'Español','it':'Italiano',
         'ru':'Русский','uk':'Українська','ja':'日本語','ar':'العربية','zh':'中文（简体）'}
LOCALE = {'en':'en_GB','fi':'fi_FI','sv':'sv_SE','de':'de_DE','fr':'fr_FR','es':'es_ES','it':'it_IT','ru':'ru_RU',
          'uk':'uk_UA','ja':'ja_JP','ar':'ar_AR','zh':'zh_CN'}
HREFLANG = {'zh':'zh-Hans'}
GC = '<script data-goatcounter="https://travelsouthgallery.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
present = [l for l in LANGS if os.path.isfile(os.path.join(ROOT, '' if l=='en' else l, 'index.html'))]
slugs = [''] + sorted(d for d in os.listdir(os.path.join(ROOT,'fi')) if os.path.isfile(os.path.join(ROOT,'fi',d,'index.html')))
def url(l, s): return BASE + ('' if l=='en' else l+'/') + (s+'/' if s else '')
def rel(frm_l, frm_s, to_l, to_s):
    depth = (0 if frm_l=='en' else 1) + (1 if frm_s else 0)
    return '../'*depth + ('' if to_l=='en' else to_l+'/') + (to_s+'/' if to_s else '') + 'index.html'
def fix(l, s):
    p = os.path.join(ROOT, '' if l=='en' else l, s, 'index.html') if s else os.path.join(ROOT, '' if l=='en' else l, 'index.html')
    h = open(p, encoding='utf-8').read(); o = h
    h = re.sub(r'<html[^>]*>', f'<html lang="{HREFLANG.get(l,l)}"' + (' dir="rtl"' if l=='ar' else '') + '>', h, count=1)
    h = re.sub(r'<link rel="(?:alternate" hreflang="[^"]*"|canonical") href="[^"]*">\n?', '', h)
    alts = f'<link rel="canonical" href="{url(l,s)}">' + ''.join(
        f'<link rel="alternate" hreflang="{HREFLANG.get(x,x)}" href="{url(x,s)}">' for x in present) + \
        f'<link rel="alternate" hreflang="x-default" href="{url("en",s)}">'
    h = re.sub(r'(</title>)', lambda m: m.group(1)+alts, h, count=1)
    h = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url(l,s)}">', h)
    h = re.sub(r'<meta property="og:locale" content="[^"]*">', f'<meta property="og:locale" content="{LOCALE[l]}">', h)
    h = re.sub(r'<meta name="robots"[^>]*>', '', h)
    def nav(cls, target_slug):
        def r(m):
            items = ''.join(
                f'<a href="{rel(l,s,x,target_slug)}" hreflang="{HREFLANG.get(x,x)}" lang="{HREFLANG.get(x,x)}"' +
                (' dir="rtl"' if x=='ar' else (' dir="ltr"' if l=='ar' else '')) +
                (' aria-current="page"' if x==l else '') + f'>{NAMES[x]}</a>' for x in present)
            return m.group(1) + items + m.group(2)
        return r
    h = re.sub(r'(<nav class="langs"[^>]*>).*?(</nav>)', nav('langs', s), h, count=1, flags=re.S)
    h = re.sub(r'(<nav class="hub-langs"[^>]*>).*?(</nav>)', nav('hub', s), h, count=1, flags=re.S)
    # GoatCounter: täsmälleen yksi
    h = h.replace(GC, '')
    h = h.replace('</body>', GC + '</body>', 1)
    # merkintä ja kuvateksti omiksi elementeikseen (tekstinä ei liimaudu)
    h = re.sub(r'(<span class="(?:photo-badge|ai-badge|tag[^"]*)">[^<]*</span>)(?=[^\s<])', r'\1 ', h)
    h = re.sub(r'(<(?:abbr|span) class="tag[^"]*"[^>]*>[^<]*</(?:abbr|span)>)(?=[^\s<])', r'\1 ', h)
    if h != o: open(p, 'w', encoding='utf-8').write(h)
    return h != o
n = sum(fix(l, s) for l in present for s in slugs if os.path.isfile(os.path.join(ROOT, '' if l=='en' else l, s, 'index.html')))
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for l in present:
    for s in slugs:
        sm.append(f'<url><loc>{url(l,s)}</loc>' + ''.join(f'<xhtml:link rel="alternate" hreflang="{HREFLANG.get(x,x)}" href="{url(x,s)}"/>' for x in present) +
                  f'<xhtml:link rel="alternate" hreflang="x-default" href="{url("en",s)}"/></url>')
sm.append('</urlset>')
open(os.path.join(ROOT,'sitemap.xml'),'w').write('\n'.join(sm)+'\n')
print(f'{n} sivua päivitetty; kielet: {", ".join(present)}; sitemap {len(present)*len(slugs)} osoitetta')
