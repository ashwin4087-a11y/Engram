from app.services.capture_storage import CaptureStorage

cs = CaptureStorage()
rec = cs.save(b'test-image-bytes', {'timestamp':'2026-07-30T00:00:00Z','distance':'1.23 m','confidence':'99.0%','fps':'30.0'})
print('saved', rec['id'], rec['path'])
print('index exists:', cs.index_file.exists())
recs = cs.list(5)
print('recent count', len(recs))
print(recs[-1] if recs else recs)
