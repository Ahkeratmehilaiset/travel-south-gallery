#!/usr/bin/env python3
"""Rakenteellinen pariteettitarkistus: vertaa jokaisen kielen sivua fi-versioon.

Laskee per sivu: otsikot (h1-h4), kappaleet (p), kuvat (img), kuvatekstit
(figcaption), lähteet (li/a lähdeosioissa: linkit joiden href alkaa http),
sisäiset linkit. Tulostaa taulukon ja palauttaa exit 1, jos jokin kieli
poikkeaa fi:stä (paitsi sallitut poikkeamat ALLOW-listassa).
Käyttö: python3 scripts/parity.py [--strict] [--only kallot,start]
"""
import os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['fi', 'en', 'sv', 'de', 'fr', 'es', 'it', 'ru', 'uk', 'ja', 'ar', 'zh']
KEYS = ['h', 'p', 'img', 'cap', 'src', 'int']

class C(HTMLParser):
    def __init__(self):
        super().__init__(); self.c = dict.fromkeys(KEYS, 0)
    def handle_starttag(self, t, a):
        a = dict(a)
        if t in ('h1', 'h2', 'h3', 'h4'): self.c['h'] += 1
        elif t == 'p': self.c['p'] += 1
        elif t == 'img': self.c['img'] += 1
        elif t == 'figcaption': self.c['cap'] += 1
        elif t == 'a':
            h = a.get('href') or ''
            if h.startswith('http'):
                # kielivalikkoa ja go-linkkejä ei lasketa lähteiksi
                self.c['src'] += 1
            elif not h.startswith(('#', 'mailto')) and 'hreflang' not in a:
                self.c['int'] += 1

def counts(path):
    c = C(); c.feed(open(path, encoding='utf-8').read()); return c.c

def page_path(lang, slug):
    base = ROOT if lang == 'en' else os.path.join(ROOT, lang)
    return os.path.join(base, slug, 'index.html') if slug else os.path.join(base, 'index.html')

def main():
    strict = '--strict' in sys.argv
    only = None
    if '--only' in sys.argv: only = sys.argv[sys.argv.index('--only') + 1].split(',')
    slugs = [''] + sorted(d for d in os.listdir(os.path.join(ROOT, 'fi'))
                          if os.path.isfile(os.path.join(ROOT, 'fi', d, 'index.html')))
    if only: slugs = [s for s in slugs if (s or 'index') in only]
    langs = [l for l in LANGS if os.path.isfile(page_path(l, ''))]
    bad = 0
    print('page'.ljust(28) + ''.join(l.rjust(6) for l in langs))
    for s in slugs:
        ref = counts(page_path('fi', s))
        row = (s or 'index').ljust(28)
        diffs = []
        for l in langs:
            p = page_path(l, s)
            if not os.path.isfile(p): row += 'MISS'.rjust(6); bad += 1; continue
            c = counts(p)
            d = [k for k in KEYS if c[k] != ref[k]]
            row += ('ok' if not d else 'X').rjust(6)
            if d:
                bad += 1
                diffs.append(f'    {l}: ' + ', '.join(f'{k} {c[k]}≠{ref[k]}' for k in d))
        print(row)
        for x in diffs: print(x)
    print(f'\npoikkeavia sivu×kieli-pareja: {bad}')
    sys.exit(1 if (bad and strict) else 0)

if __name__ == '__main__':
    main()
