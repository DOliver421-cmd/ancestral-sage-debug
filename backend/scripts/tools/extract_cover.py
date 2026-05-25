"""Extract cover image from the Black On Black Love PDF."""
import os, sys
from PyPDF2 import PdfReader

base = os.path.expanduser('~/Downloads')
path = os.path.join(base, 'Black On Black Love by NAM Oshun - Copy.pdf')

reader = PdfReader(path)

for pg_num in [0, 1]:
    page = reader.pages[pg_num]
    res = page.get('/Resources', {})
    while hasattr(res, 'get_object'):
        res = res.get_object()
    xobj = res.get('/XObject', {})
    found = False
    for name in xobj:
        obj = xobj[name]
        while hasattr(obj, 'get_object'):
            obj = obj.get_object()
        subtype = obj.get('/Subtype', '')
        print('Page %d: %s subtype=%s' % (pg_num, name, subtype))
        if subtype == '/Image':
            w = obj.get('/Width', 0)
            h = obj.get('/Height', 0)
            filt = obj.get('/Filter', '')
            print('  Image %dx%d filter=%s' % (w, h, filt))
            data = obj.get_data()
            ext = 'jpg' if filt == '/DCTDecode' else 'png'
            out = os.path.join(base, 'cover_%s.%s' % (name, ext))
            with open(out, 'wb') as f:
                f.write(data)
            print('  Saved %s (%d bytes)' % (out, len(data)))
            found = True
    if not found:
        print('Page %d: no images found' % pg_num)
