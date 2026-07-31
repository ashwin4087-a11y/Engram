import urllib.request, ssl, sys
base='http://127.0.0.1:8000'
paths=['/','/js/app.js','/js/router.js','/js/pages/index.js','/css/globals.css']
ctx=ssl.create_default_context()
for p in paths:
    try:
        req=urllib.request.Request(base+p, headers={'User-Agent':'python'})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            print('URL',p,'STATUS',r.status,'CT',r.headers.get('Content-Type'))
            body=r.read(1000).decode('utf-8','replace').replace('\n',' ')
            print(body[:800])
    except Exception as e:
        print('URL',p,'ERROR',e)
        sys.exit(2)
print('OK')
