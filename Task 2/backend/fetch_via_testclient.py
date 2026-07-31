from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for p in ['/','/js/app.js','/css/globals.css']:
    r=c.get(p)
    print('URL',p,'STATUS',r.status_code,'CT',r.headers.get('content-type'))
    print(r.text[:800])
