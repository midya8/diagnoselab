"""Original synthetic CNF controls; no external data or solver code."""
import json
import random
from pathlib import Path
from diagnoselab import audit


def make(n, soft, costs=None, hard=None):
    return {'variables': n, 'hard': hard or [], 'soft': [{'clause': c, 'cost': str((costs or ['1'] * len(soft))[i])} for i, c in enumerate(soft)]}


def cases():
    rows = [
        ('Minimal is not cheapest or smallest', make(3, [[1], [-2], [-2], [3, -3]], ['5', '1', '1', '2'], [[-1, 2]])),
        ('Two disjoint conflicts: one core is not enough', make(2, [[1], [-1], [2], [-2]])),
        ('No units: branch both ways to refute', make(2, [[1, 2], [1, -2], [-1, 2], [-1, -2]])),
        ('Background itself is inconsistent', make(2, [[2], [-2]], hard=[[1], [-1]])),
        ('Empty hard clause cannot be repaired', make(2, [[1]], hard=[[]])),
        ('Every soft empty clause must go', make(2, [[], [], [1]], ['1/3', '2/3', '1'])),
        ('Tautologies and repeated literals retain identities', make(2, [[1, 1], [-1, -1], [1, -1], [1, 1]], ['3/2', '2', '1', '1/2'])),
        ('Already satisfiable: only the empty repair', make(3, [[1, 2], [-1, 3], [-2, 3]])),
        ('No removable clauses, satisfiable background', make(3, [], hard=[[1, 2]])),
        ('Deletion order chooses different-sized cores', make(3, [[1], [-1], [2], [-2, 3], [-3]])),
        ('Unused variables multiply truth-table models', make(6, [[1], [-1]])),
        ('Six-variable implication chain', make(6, [[1], [-1, 2], [-2, 3], [-3, 4], [-4, 5], [-5, 6], [-6]], ['1/2', '2/3', '3/4', '4/5', '5/6', '6/7', '7/8'])),
    ]
    rows.append(('Maximum declared bounds: four independent conflicts', make(6, [[1], [-1], [2], [-2], [3], [-3], [4], [-4]], hard=[[1,-1] for _ in range(8)])))
    rng = random.Random(9417)
    for k in range(5):
        n = 3 + k % 2
        soft = [[rng.choice([-1, 1]) * v for v in rng.sample(range(1, n+1), rng.randint(1, 3))] for _ in range(6)]
        rows.append((f'Seeded signed constraints {k+1}', make(n, soft, [f'{rng.randint(1, 7)}/{rng.randint(1, 5)}' for _ in soft])))
    return rows


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    rows = [{'name': name, 'input': p, 'report': audit(p)} for name, p in cases()]
    (root / 'docs/audits.json').write_text(json.dumps(rows, separators=(',', ':')) + '\n')
    (root / 'examples/demo.json').write_text(json.dumps(rows[0]['input'], indent=2) + '\n')
    print(json.dumps({'cases': len(rows), 'subsets': sum(r['report']['checks']['subsets'] for r in rows), 'nodes': sum(r['report']['checks']['dpll_nodes'] for r in rows), 'mus': sum(len(r['report']['mus']) for r in rows), 'mcs': sum(len(r['report']['mcs']) for r in rows)}))
