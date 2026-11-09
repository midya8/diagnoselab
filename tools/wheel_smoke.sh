#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
uv build --wheel --out-dir "$TMP/dist" "$ROOT" >/dev/null
uv venv --python 3.10 "$TMP/env" >/dev/null
uv pip install --python "$TMP/env/bin/python" "$TMP"/dist/*.whl >/dev/null
cp "$ROOT/tools/verify_installed.py" "$TMP/check.py"
cd "$TMP"
unset PYTHONPATH
"$TMP/env/bin/python" check.py "$ROOT/docs/audits.json" "$ROOT"
"$TMP/env/bin/diagnoselab" "$ROOT/examples/demo.json" --output "$TMP/console.json"
"$TMP/env/bin/python" -m diagnoselab "$ROOT/examples/demo.json" --output "$TMP/module.json"
cmp "$TMP/console.json" "$TMP/module.json"
echo 'Installed console/module CLI and all 18 reports/four origins passed'
