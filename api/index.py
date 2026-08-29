"""Vercel entry point — every backend module behind one serverless function.

The frontend calls same-origin paths (/journey, /gov, /identity, /academy,
/bol); vercel.json rewrites them here and this dispatcher hands each request
to the owning module's FastAPI app. Module boundaries stay intact — this file
only routes, it never reaches into a module.

Serverless caveat (documented in the README): the SQLite state lives in /tmp,
which persists per warm instance but not across cold starts or instances. For
durable state, host the services on a persistent box and point the frontend's
VITE_* URLs at it.
"""

import os

# Serverless filesystems are read-only outside /tmp, and sibling services are
# reached by calling this same deployment back over HTTP.
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

from academy_service.main import app as academy_app  # noqa: E402
from bol_ke_apply.api import app as bol_app  # noqa: E402
from gateway_service.main import app as gateway_app  # noqa: E402
from identity_service.main import app as identity_app  # noqa: E402
from journey_service.main import app as journey_app  # noqa: E402

ROUTES = {
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

    body = b'{"status":"ok","modules":["journey","gateway","identity","academy","bol-ke-apply"]}'
    await send(
        {
            "type": "http.response.start",
            "status": 200 if path in ("/", "/healthz") else 404,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})
