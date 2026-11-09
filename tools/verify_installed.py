"""Run this outside the checkout with an installed wheel."""
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from diagnoselab import audit

rows = json.loads(Path(sys.argv[1]).read_text())
checkout = Path(sys.argv[2]).resolve()
origins = {}
for name in ['diagnoselab', 'diagnoselab.core', 'diagnoselab.cli', 'diagnoselab.__main__']:
    if name.endswith('__main__'):
        origin = importlib.util.find_spec(name).origin
    else:
        origin = importlib.import_module(name).__file__
    assert not Path(origin).resolve().is_relative_to(checkout), origin
    origins[name] = origin
for row in rows:
    assert audit(row['input']) == row['report'], row['name']
print(json.dumps({'reports': len(rows), 'module_origins': origins}))
