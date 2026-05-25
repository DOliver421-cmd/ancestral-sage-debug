import os, sys
base = os.path.expanduser(r'~\Downloads')
path = os.path.join(base, 'Black On Black Love by NAM Oshun - Copy.pdf')

from PyPDF2 import PdfReader
reader = PdfReader(path)

for pg in range(min(3, len(reader.pages))):
    page = reader.pages[pg]
    res = page.get('/Resources', {})
    xobj = res.get('/XObject', {})
    for name in xobj:
        obj = xobj[name]
        subtype = obj.get('/Subtype', '')
        w = obj.get('/Width', '?')
        h = obj.get('/Height', '?')
        filt = obj.get('/Filter', '?')
        print(f'Page {pg}: {name} subtype={subtype} {w}x{h} filter={filt}')
