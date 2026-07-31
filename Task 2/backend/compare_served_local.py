import hashlib, urllib.request, ssl, sys, pathlib
base='http://127.0.0.1:8000'
path='/js/app.js'
ctx=ssl.create_default_context()
local=pathlib.Path('../frontend/js/app.js').resolve()
print('Local file:', local)
with open(local,'rb') as f:
    local_bytes=f.read()
    print('local len', len(local_bytes))
    print('local md5', hashlib.md5(local_bytes).hexdigest())
try:
    req=urllib.request.Request(base+path, headers={'User-Agent':'python'})
    with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
        served=r.read()
        print('served len', len(served))
        print('served md5', hashlib.md5(served).hexdigest())
        # print first 400 bytes
        print('served head:', served[:400])
except Exception as e:
    print('Error fetching:', e)
    sys.exit(2)
if local_bytes==served:
    print('MATCH')
else:
    print('DIFFER')
    # show diff-ish
    for i,(a,b) in enumerate(zip(local_bytes,served)):
        if a!=b:
            print('first diff at', i, 'local', chr(a), 'served', chr(b))
            break
