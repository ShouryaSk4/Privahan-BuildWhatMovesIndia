#!/usr/bin/env bash
# Post-merge type generation (AGENTS.md §4.3 / §8.5):
#   Pydantic models -> FastAPI -> OpenAPI -> openapi-typescript -> TS types.
#
# All four backend services are real now, so every schema comes from the
# service that owns it. No hand-written TypeScript duplicates anywhere.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OPENAPI_DIR="$ROOT/packages/contracts/openapi"
TYPES_DIR="$ROOT/apps/web/src/api/types"
mkdir -p "$OPENAPI_DIR" "$TYPES_DIR"
cd "$ROOT"

dump() { # dump <import-path> <out-name>
  uv run python -c "import json,importlib; m=importlib.import_module('$1'); print(json.dumps(m.app.openapi()))" \
    > "$OPENAPI_DIR/$2.json"
}

echo "-- exporting OpenAPI schemas"
dump journey_service.main   journey    # Module 2
dump gateway_service.main   gateway    # Module 5
dump identity_service.main  identity   # Module 3
dump academy_service.main   academy    # Module 4

echo "-- generating TypeScript types"
cd "$ROOT/apps/web"
for name in journey gateway identity academy; do
  pnpm exec openapi-typescript "$OPENAPI_DIR/$name.json" -o "$TYPES_DIR/$name.ts"
done
echo "-- done: $TYPES_DIR"
