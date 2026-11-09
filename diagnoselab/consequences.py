"""Repair-policy consequences for a single propositional query clause."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .core import audit, clause, dpll, parse


def consequences(raw, query):
    base = audit(raw)
    p = base['input']
    n, m = p['variables'], len(p['soft'])
    q = clause(query, n)
    all_mask = (1 << m) - 1
    def holds(model, literals):
        return any(((model >> (abs(l)-1)) & 1) == int(l > 0) for l in literals)
    def inspect(kept_mask):
        models = base['subsets'][kept_mask]['models']
        true = [v for v in models if holds(v, q)]
        false = [v for v in models if not holds(v, q)]
        cs = [c for c in base['clauses'] if c['kind'] == 'hard' or kept_mask & (1 << int(c['id'][1:]))]
        negated = [{'id': 'q'+str(i), 'kind': 'query_negation', 'literals': [-l], 'normalized': [-l], 'tautology': False} for i, l in enumerate(q)]
        solve = dpll(n, cs + negated)
        assert solve['sat'] == bool(false)
        assert solve['model'] is None or solve['model'] in false
        return {'kept_mask': kept_mask, 'models': list(models), 'query_true_models': true, 'countermodels': false, 'entailed': not false, 'possible': bool(true), 'negated_query_clauses': cs + negated, 'negated_query_dpll': solve}
    repairs = []
    for repair in base['mcs']:
        repairs.append({'removed_mask': repair['mask'], 'removed': repair['removed'], 'cost': repair['cost'], **inspect(repair['kept_mask'])})
    policies = []
    for name, masks in [('all_minimal', [r['removed_mask'] for r in repairs]), ('minimum_cost', base['selection']['cost_masks']), ('minimum_cardinality', base['selection']['cardinality_masks'])]:
        selected = [r for r in repairs if r['removed_mask'] in masks]
        union = sorted({v for r in selected for v in r['models']})
        common = all_mask
        for r in selected:
            common &= r['kept_mask']
        removed_union = 0
        removed_intersection = all_mask
        for r in selected:
            removed_union |= r['removed_mask']
            removed_intersection &= r['removed_mask']
        literal_rows = []
        for i in range(n):
            for literal in [i+1, -(i+1)]:
                yes = [v for v in union if holds(v, [literal])]
                no = [v for v in union if not holds(v, [literal])]
                literal_rows.append({'literal': literal, 'all_models': not no if selected else None, 'some_model': bool(yes) if selected else None, 'witness_model': yes[0] if yes else None, 'countermodel': no[0] if no else None})
        inter = inspect(common) if selected else None
        every = all(r['entailed'] for r in selected) if selected else None
        some = any(r['entailed'] for r in selected) if selected else None
        if selected:
            assert not inter['entailed'] or every
            assert not every or some
        policies.append({'name': name, 'applicable': bool(selected), 'repair_masks': list(masks), 'models_union': union, 'entailed_every_repair': every, 'entailed_some_repair': some, 'possible_every_repair': all(r['possible'] for r in selected) if selected else None, 'possible_some_repair': any(r['possible'] for r in selected) if selected else None, 'entailing_repairs': [r['removed_mask'] for r in selected if r['entailed']], 'nonentailing_repairs': [r['removed_mask'] for r in selected if not r['entailed']], 'possible_repairs': [r['removed_mask'] for r in selected if r['possible']], 'impossible_repairs': [r['removed_mask'] for r in selected if not r['possible']], 'removed_in_every_repair': removed_intersection if selected else None, 'removed_in_some_repair': removed_union if selected else None, 'kept_in_every_repair': common if selected else None, 'literal_consequences': literal_rows, 'intersection_baseline': inter})
    return {'schema': 'diagnoselab/consequences/1', 'input': p, 'query': q, 'selection': base['selection'], 'repairs': repairs, 'policies': policies, 'checks': {'hard_satisfiable': base['checks']['hard_satisfiable'], 'repairs': len(repairs), 'negated_query_nodes': sum(len(r['negated_query_dpll']['trace']) for r in repairs) + sum(len(p['intersection_baseline']['negated_query_dpll']['trace']) for p in policies if p['intersection_baseline'] is not None), 'truth_dpll_agree': True, 'intersection_every_some_chain': True}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input')
    ap.add_argument('--query', required=True, help='JSON array for one disjunctive clause')
    ap.add_argument('--output')
    args = ap.parse_args()
    try:
        report = consequences(parse(Path(args.input).read_text()), json.loads(args.query))
        text = json.dumps(report, indent=2) + '\n'
        if args.output:
            Path(args.output).write_text(text)
        else:
            print(text, end='')
    except (ValueError, OSError) as exc:
        ap.exit(2, f'Invalid input: {exc}\n')


if __name__ == '__main__':
    main()
