#!/usr/bin/env bash
# Post-merge type generation (AGENTS.md §8.5):
#   Pydantic models -> FastAPI -> OpenAPI -> openapi-typescript -> TS types.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OPENAPI_DIR="$ROOT/packages/contracts/openapi"
TYPES_DIR="$ROOT/apps/web/src/api/types"
mkdir -p "$OPENAPI_DIR" "$TYPES_DIR"

echo "-- exporting OpenAPI schemas"
(cd "$ROOT/services/journey" && uv run python -c \
  "import json; from app.main import app; print(json.dumps(app.openapi()))" \
  > "$OPENAPI_DIR/journey.json")
(cd "$ROOT/services/gateway" && uv run python -c \
  "import json; from app.main import app; print(json.dumps(app.openapi()))" \
  > "$OPENAPI_DIR/gateway.json")
(cd "$ROOT/services/journey" && uv run python "$ROOT/tools/contracts_openapi.py" \
  > "$OPENAPI_DIR/contracts.json")

echo "-- generating TypeScript types"
cd "$ROOT/apps/web"
pnpm exec openapi-typescript "$OPENAPI_DIR/journey.json" -o "$TYPES_DIR/journey.ts"
pnpm exec openapi-typescript "$OPENAPI_DIR/gateway.json" -o "$TYPES_DIR/gateway.ts"
pnpm exec openapi-typescript "$OPENAPI_DIR/contracts.json" -o "$TYPES_DIR/contracts.ts"
echo "-- done: $TYPES_DIR"
