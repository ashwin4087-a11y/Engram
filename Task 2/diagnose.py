import sys
import os
import traceback
import inspect
import re
from pathlib import Path
from html.parser import HTMLParser

# Setup pathing
WORKSPACE_ROOT = Path(__file__).parent.resolve()
FRONTEND_DIR = WORKSPACE_ROOT / "frontend"
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

results = []

def log(section_title, content_list=None):
    results.append(f"=== {section_title} ===")
    if content_list:
        results.extend(content_list)
    results.append("")

# 1. Environment
env_list = [
    f"Python Executable: {sys.executable}",
    f"Python Version: {sys.version}",
]
try:
    import fastapi
    env_list.append(f"FastAPI Version: {fastapi.__version__}")
except Exception as e:
    env_list.append(f"FastAPI Version: Failed to import/get version ({e})")

try:
    import starlette
    env_list.append(f"Starlette Version: {starlette.__version__}")
except Exception as e:
    env_list.append(f"Starlette Version: Failed to import/get version ({e})")

log("1. Environment", env_list)

# Try importing the app
app = None
app_import_error = None
try:
    from app.main import app
except Exception as e:
    app_import_error = traceback.format_exc()
    log("App Import Error", [app_import_error])

# 2. Route Validation
route_list = []
if app:
    for route in app.routes:
        methods = ",".join(route.methods) if hasattr(route, "methods") and route.methods else "N/A"
        endpoint_name = route.endpoint.__name__ if hasattr(route, "endpoint") else str(route.endpoint)
        route_list.append(f"Route: {route.path:30} Methods: {methods:15} Endpoint: {endpoint_name}")
else:
    route_list.append("FastAPI application not loaded. Cannot list routes.")
log("2. Registered FastAPI Routes", route_list)

# 3. TestClient Setup
client = None
if app:
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
    except Exception as e:
        log("TestClient Initialization Error", [traceback.format_exc()])

# Helper to fetch and log response
def test_endpoint(path, is_backend=False):
    if not client:
        return [f"URL: {path} -> SKIP (TestClient not initialized)"]
    
    try:
        # Special handling for MJPEG endpoint to prevent hanging on infinite stream
        if path == "/preview":
            # We can request it with a timeout or use a custom stream reader
            # Or just check if the route exists and test generator function directly.
            # But let's try calling client.get with a short stream/headers check.
            response = client.get(path, stream=True)
            res_list = [
                f"URL: {path}",
                f"HTTP Status: {response.status_code}",
                f"Content-Type: {response.headers.get('content-type')}",
                f"Content-Length: {response.headers.get('content-length')}"
            ]
            response.close()
            return res_list
            
        response = client.get(path, follow_redirects=False)
        res_list = [
            f"URL: {path}",
            f"HTTP Status: {response.status_code}",
            f"Content-Type: {response.headers.get('content-type')}",
            f"Content-Length: {response.headers.get('content-length')}",
        ]
        
        # Redirect check
        if response.status_code in (301, 302, 303, 307, 308):
            res_list.append(f"Redirect Location: {response.headers.get('location')}")
            
        if is_backend:
            # Body preview
            try:
                body_json = response.json()
                res_list.append(f"Response JSON: {repr(body_json)[:300]}")
            except Exception:
                res_list.append(f"Response Text (truncated): {repr(response.text[:200])}")
        else:
            # Frontend preview
            res_list.append(f"Content Preview (first 100 chars): {repr(response.text[:100])}")
            
        return res_list
    except Exception as e:
        return [
            f"URL: {path} -> FAILED",
            f"Exception: {e}",
            f"Traceback:\n{traceback.format_exc()}"
        ]

# 4. Frontend Responses
fe_urls = ["/", "/index.html", "/js/app.js", "/js/router.js", "/js/api.js", "/css/globals.css"]
fe_results = []
for url in fe_urls:
    fe_results.extend(test_endpoint(url, is_backend=False))
    fe_results.append("-" * 50)
log("3. Frontend Response Verification", fe_results)

# 5. Backend Endpoints
be_urls = ["/health", "/metrics", "/estimate", "/preview", "/calibration"]
be_results = []
for url in be_urls:
    be_results.extend(test_endpoint(url, is_backend=True))
    be_results.append("-" * 50)
log("4. Backend Endpoints Verification", be_results)

# 6. HTML Parser to extract JS modules and CSS files
class IndexParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.modules = []
        self.css_files = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "script" and attrs_dict.get("type") == "module" and "src" in attrs_dict:
            self.modules.append(attrs_dict["src"])
        elif tag == "link" and attrs_dict.get("rel") == "stylesheet" and "href" in attrs_dict:
            self.css_files.append(attrs_dict["href"])

html_parser = IndexParser()
index_path = FRONTEND_DIR / "index.html"
html_exists = index_path.exists()
if html_exists:
    with open(index_path, "r", encoding="utf-8") as f:
        html_parser.feed(f.read())
else:
    log("Parser Error", ["index.html not found!"])

# 7. Static File Validation
static_val_list = []
if html_exists:
    static_val_list.append("HTML referenced assets:")
    # Validate CSS
    for css in html_parser.css_files:
        local_file = FRONTEND_DIR / css
        exists = local_file.exists()
        static_val_list.append(f"CSS Link: {css:30} Local Exists: {str(exists):6} Served Status: {client.get('/' + css).status_code if client else 'N/A'}")
    # Validate JS module scripts
    for js in html_parser.modules:
        local_file = FRONTEND_DIR / js
        exists = local_file.exists()
        static_val_list.append(f"JS Link:  {js:30} Local Exists: {str(exists):6} Served Status: {client.get('/' + js).status_code if client else 'N/A'}")
else:
    static_val_list.append("HTML not present to validate static files.")
log("5. HTML Static File Reference Validation", static_val_list)

# 8. JS Module dependency validation (recursively check imports)
IMPORT_RE = re.compile(r'(?:import|export)\s+(?:.*from\s+)?[\'"]([^\'"]+)[\'"]')

js_resolved = {}
js_to_resolve = []

# Populate initial JS modules from HTML
for script in html_parser.modules:
    js_to_resolve.append((script, FRONTEND_DIR / script))

module_val_list = []

while js_to_resolve:
    rel_path, abs_path = js_to_resolve.pop(0)
    if rel_path in js_resolved:
        continue
    
    if not abs_path.exists():
        js_resolved[rel_path] = "MISSING"
        module_val_list.append(f"Module: {rel_path} -> MISSING locally!")
        continue
        
    js_resolved[rel_path] = "OK"
    module_val_list.append(f"Module: {rel_path} -> FOUND")
    
    # Read imports
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        imports = IMPORT_RE.findall(content)
        for imp in imports:
            # Resolve relative import path
            parent_dir = abs_path.parent
            resolved_abs = (parent_dir / imp).resolve()
            
            # Compute relative to frontend dir for keys
            try:
                resolved_rel = "js/" + str(resolved_abs.relative_to(FRONTEND_DIR / "js")).replace("\\", "/")
            except Exception:
                resolved_rel = imp # fallback
                
            module_val_list.append(f"  Imports: {imp} (resolves to: {resolved_rel})")
            
            if resolved_rel not in js_resolved:
                js_to_resolve.append((resolved_rel, resolved_abs))
    except Exception as e:
        module_val_list.append(f"  Error reading imports of {rel_path}: {e}")

log("6. Recursive ES Module Validation", module_val_list)

# 9. Preview Endpoint Detailed Inspection
preview_ins_list = []
try:
    import app.api.preview as preview_module
    preview_ins_list.append("Loaded app.api.preview module successfully.")
    
    # Check imports
    preview_ins_list.append("Inspecting preview.py variables:")
    for v in ["cv2", "asyncio", "tracker_service", "apply_overlays", "settings", "TrackerStatus"]:
        has_v = hasattr(preview_module, v)
        preview_ins_list.append(f"  Has '{v}': {has_v}")
        
    # Check specifically for "time"
    has_time = hasattr(preview_module, "time")
    preview_ins_list.append(f"  Has 'time' module imported: {has_time}")
    
    # Check function generate_frames code
    from app.api.preview import generate_frames
    source = inspect.getsource(generate_frames)
    preview_ins_list.append("  generate_frames code calls:")
    if "time.sleep" in source:
        preview_ins_list.append("    [BUG] Calls 'time.sleep'. This blocks the event loop and will crash with NameError if 'time' is not imported.")
    if "asyncio.sleep" in source:
        preview_ins_list.append("    Calls 'asyncio.sleep'. (Correct asynchronous behavior)")
        
except Exception as e:
    preview_ins_list.append(f"Failed to load/inspect preview module: {e}")
    preview_ins_list.append(traceback.format_exc())

log("7. Preview Endpoint Implementation Validation", preview_ins_list)

# 10. Summary & Classification of Issues
issues_summary = []
blocking_issues = []
major_issues = []
minor_issues = []

# Classify MIME Type issue
# Let's inspect the headers from JS endpoints
mimetype_blocked = False
js_wrong_mimetypes = []

for url in ["/js/app.js", "/js/router.js", "/js/api.js"]:
    if client:
        try:
            r = client.get(url)
            ct = r.headers.get("content-type", "")
            if not ct or not ("javascript" in ct or "ecmascript" in ct):
                mimetype_blocked = True
                js_wrong_mimetypes.append(f"{url} served with Content-Type: '{ct}'")
        except Exception:
            pass

if mimetype_blocked:
    blocking_issues.append("BLOCKED BY MIME TYPE: ES Modules loaded with <script type=\"module\"> must be served with a JavaScript MIME type. Currently, JS modules are served with non-JavaScript Content-Types (e.g. text/plain or text/html). Modern browsers (Chrome, Edge, etc.) enforce strict MIME type checking and block execution completely, rendering a white/blank screen.")
    for detail in js_wrong_mimetypes:
        blocking_issues.append(f"  Evidence: {detail}")
else:
    minor_issues.append("MIME Types for JS appear correct in TestClient (could still vary in production browser depend on host system registry).")

# Check if app had import errors
if app_import_error:
    blocking_issues.append(f"APPLICATION CRASH ON IMPORT: The backend failed to import: {app_import_error}")

# Check preview endpoint time bug
if 'preview_module' in locals() and not has_time:
    # Check if code uses time.sleep
    if "time.sleep" in source:
        major_issues.append("PREVIEW ENDPOINT CRASH: app/api/preview.py calls 'time.sleep()' inside generator, but the 'time' module is never imported. Running the camera stream page will crash the backend preview generator immediately with NameError. (Does not block main dashboard index page load, but breaks the live preview stream).")

# Check any other missing files in modules
for rel, status in js_resolved.items():
    if status == "MISSING":
        blocking_issues.append(f"MISSING MODULE FILE: Frontend script imports {rel}, but the file does not exist on disk!")

# Output Summary
issues_summary.append("BLOCKED / BLOCKING ISSUES (Prevent UI rendering):")
if blocking_issues:
    for b in blocking_issues:
        issues_summary.append(f"  - {b}")
else:
    issues_summary.append("  - None detected.")
issues_summary.append("")

issues_summary.append("MAJOR ISSUES (Cause runtime crashes or break major functionality):")
if major_issues:
    for m in major_issues:
        issues_summary.append(f"  - {m}")
else:
    issues_summary.append("  - None detected.")
issues_summary.append("")

issues_summary.append("MINOR ISSUES / telemetry:")
if minor_issues:
    for mn in minor_issues:
        issues_summary.append(f"  - {mn}")
else:
    issues_summary.append("  - None detected.")

log("8. Diagnostic Summary", issues_summary)

# Write out diagnostic results
output_file = WORKSPACE_ROOT / "diagnose_results.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print(f"Comprehensive diagnostics written to: {output_file.name}")
print("Please run this command: python diagnose.py")
