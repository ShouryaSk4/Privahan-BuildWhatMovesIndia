"""Vercel entry point — every backend module behind one serverless function.

The frontend calls same-origin paths (/journey, /gov, /identity, /academy,
/bol); vercel.json rewrites them here and this dispatcher hands each request
to the owning module's FastAPI app. Module boundaries stay intact — this file
only routes, it never reaches into a module.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Add all internal package source directories to sys.path for Vercel serverless execution
src_paths = [
    ROOT_DIR / "packages" / "contracts",
    ROOT_DIR / "services" / "identity" / "src",
    ROOT_DIR / "services" / "academy" / "src",
    ROOT_DIR / "services" / "bol-ke-apply" / "src",
    ROOT_DIR / "services" / "journey" / "src",
    ROOT_DIR / "services" / "gateway" / "src",
]
for p in src_paths:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Serverless filesystems are read-only outside /tmp, and sibling services are
# reached directly in-process or over HTTP.
os.environ["IDENTITY_MODE"] = "direct"
os.environ["GATEWAY_MODE"] = "direct"
# Bol Ke Apply shares this process with the journey app — call it in-process
# instead of over HTTPS back to our own deployment URL (which stalls the agent).
os.environ["JOURNEY_MODE"] = "direct"
os.environ.setdefault("JOURNEY_DB", "/tmp/journey.sqlite3")
os.environ.setdefault("GATEWAY_DB", "/tmp/gateway.sqlite3")
os.environ.setdefault("JOURNEY_FAST_FORWARD", "1")  # demo: collapse waiting periods

_self = os.environ.get("VERCEL_URL", "")
if _self:
    base = f"https://{_self}"
    os.environ.setdefault("IDENTITY_URL", base)
    os.environ.setdefault("GATEWAY_URL", base)
    os.environ.setdefault("IDENTITY_SERVICE_URL", base)
    os.environ.setdefault("ACADEMY_SERVICE_URL", base)
    os.environ.setdefault("JOURNEY_SERVICE_URL", base)

from academy_service.main import app as academy_app
from bol_ke_apply.api import app as bol_app
from gateway_service.main import app as gateway_app
from identity_service.main import app as identity_app
from journey_service.main import app as journey_app

ROUTES = {
    # /session mints the ownership token the hardened journey routes require —
    # it MUST be routed (and rewritten in vercel.json) or the whole flow dies
    # at sign-in with an edge 404.
    "/session": journey_app,
    "/journey": journey_app,
    "/gov": gateway_app,
    "/identity": identity_app,
    "/academy": academy_app,
}


async def app(scope, receive, send):
    if scope["type"] != "http":
        return
    path = scope.get("path", "/")

    for prefix, target in ROUTES.items():
        if path == prefix or path.startswith(prefix + "/"):
            await target(scope, receive, send)
            return

    if path == "/bol" or path.startswith("/bol/"):
        scope = dict(scope)
        scope["path"] = path[len("/bol") :] or "/"
        await bol_app(scope, receive, send)
        return

    try:
        from journey_service.engine import get_engine

        storage = get_engine().store.backend_name
    except Exception:  # noqa: BLE001 — health must answer even if the store cannot
        storage = "unknown"
    commit = os.environ.get("VERCEL_GIT_COMMIT_SHA", "local")[:7]
    body = (
        '{"status":"ok","modules":["journey","gateway","identity","academy","bol-ke-apply"],'
        f'"storage":"{storage}","commit":"{commit}"}}'
    ).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 200 if path in ("/", "/healthz") else 404,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})
