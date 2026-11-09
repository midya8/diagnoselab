"""Original policy/query controls, including strict quantifier separations."""
import json
from pathlib import Path
from tools.build_audits import cases, make
from diagnoselab.consequences import consequences


def controls():
    rows = [(name, p, [1]) for name, p in cases()]
    rows.extend([
        ('Empty query is false, not unknown', make(2, [[1], [-1]]), []),
        ('Tautological query is true in every surviving model', make(2, [[1], [-1]]), [2, -2]),
        ('Repeated query literal keeps equivalent meaning', make(2, [[1], [-1]]), [1, 1]),
        ('Possible in every repair does not mean any repair entails it', make(2, [[1], [-1]]), [2]),
        ('Every repair entails, intersection of kept clauses does not', make(3, [[1], [2], [3]], hard=[[-1,-2],[-1,-3],[-2,-3]]), [1, 2, 3]),
        ('Different repairs support a disjunction with no shared cause', make(2, [[1], [2]], hard=[[-1, -2]]), [1, 2]),
        ('Negated query needs both false and true branches to refute', make(3, [], hard=[[1,2,3],[1,-2,3],[-1,2,3],[-1,-2,3]]), [3]),
        ('Empty query countermodel requires satisfiable branching', make(2, [], hard=[[1,2]]), []),
    ])
    return rows


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    rows = [{'name': name, 'input': p, 'query': q, 'report': consequences(p, q)} for name, p, q in controls()]
    (root/'docs/consequences-audits.json').write_text(json.dumps(rows, separators=(',', ':'))+'\n')
    print(json.dumps({'controls': len(rows), 'repairs': sum(len(r['report']['repairs']) for r in rows), 'nodes': sum(r['report']['checks']['negated_query_nodes'] for r in rows), 'policies': 3*len(rows)}))
