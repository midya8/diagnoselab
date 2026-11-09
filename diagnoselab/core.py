from __future__ import annotations

import json
import re
from fractions import Fraction as Q

MAX_BYTES = 32768


def integer(x, lo, hi, name):
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError(f'{name} must be an integer in [{lo},{hi}]')
    return x


def rational(x):
    if not isinstance(x, str) or not re.fullmatch(r'-?(?:0|[1-9][0-9]{0,5})(?:/[1-9][0-9]{0,5})?', x):
        raise ValueError('cost must be a bounded positive rational string')
    q = Q(x)
    if q <= 0 or q > 10000:
        raise ValueError('cost must be >0 and <=10000')
    return str(q)


def clause(x, n):
    if not isinstance(x, list) or len(x) > 12:
        raise ValueError('clause must be a list with at most 12 literals')
    return [integer(v, -n, n, 'literal') if v != 0 else (_ for _ in ()).throw(ValueError('literal cannot be zero')) for v in x]


def validate(x):
    if not isinstance(x, dict) or set(x) != {'variables', 'hard', 'soft'}:
        raise ValueError('expected exactly variables, hard and soft')
    n = integer(x['variables'], 1, 6, 'variables')
    if not isinstance(x['hard'], list) or len(x['hard']) > 8:
        raise ValueError('hard must contain at most eight clauses')
    if not isinstance(x['soft'], list) or len(x['soft']) > 8:
        raise ValueError('soft must contain at most eight removable clauses')
    hard = [clause(c, n) for c in x['hard']]
    soft = []
    for c in x['soft']:
        if not isinstance(c, dict) or set(c) != {'clause', 'cost'}:
            raise ValueError('soft entry requires exactly clause and cost')
        soft.append({'clause': clause(c['clause'], n), 'cost': rational(c['cost'])})
    return {'variables': n, 'hard': hard, 'soft': soft}


def parse(text):
    if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_BYTES:
        raise ValueError('JSON exceeds 32768 UTF-8 bytes')
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError('duplicate JSON key')
            out[k] = v
        return out
    return validate(json.loads(text, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON'))))


def records(p):
    rows = []
    for kind, cs in [('hard', p['hard']), ('soft', [s['clause'] for s in p['soft']])]:
        for i, c in enumerate(cs):
            norm = sorted(set(c), key=lambda l: (abs(l), l))
            rows.append({'id': ('h' if kind == 'hard' else 's') + str(i), 'kind': kind, 'literals': list(c), 'normalized': norm, 'tautology': any(-l in norm for l in norm)})
    return rows


def dpll(n, clauses):
    trace = []
    def residual(a):
        active, satisfied = [], []
        for c in clauses:
            if c['tautology'] or any(a[abs(l)-1] is not None and a[abs(l)-1] == int(l > 0) for l in c['normalized']):
                satisfied.append(c['id'])
            else:
                active.append({'id': c['id'], 'literals': [l for l in c['normalized'] if a[abs(l)-1] is None]})
        return active, satisfied
    def visit(initial, parent):
        a = list(initial)
        node = {'id': len(trace), 'parent': parent, 'initial': list(a), 'steps': [], 'assignment': None, 'residual': None, 'satisfied_ids': None, 'kind': None, 'conflict_clause': None, 'split_variable': None, 'children': [], 'model': None}
        trace.append(node)
        while True:
            active, satisfied = residual(a)
            conflict = next((c for c in active if not c['literals']), None)
            if conflict is not None:
                node['kind'] = 'conflict'; node['conflict_clause'] = conflict['id']; break
            if not active:
                node['kind'] = 'model'; node['model'] = sum((v or 0) << i for i, v in enumerate(a)); break
            unit = next((c for c in active if len(c['literals']) == 1), None)
            if unit is not None:
                literal = unit['literals'][0]
                a[abs(literal)-1] = int(literal > 0)
                node['steps'].append({'clause_id': unit['id'], 'literal': literal, 'assignment_after': list(a)})
                continue
            node['kind'] = 'split'
            var = min(abs(l) for c in active for l in c['literals']) - 1
            node['split_variable'] = var
            for bit in [0, 1]:
                child = list(a); child[var] = bit
                child_id, model = visit(child, node['id'])
                node['children'].append(child_id)
                if model is not None:
                    node['model'] = model
                    break
            break
        node['assignment'] = list(a)
        node['residual'] = active
        node['satisfied_ids'] = satisfied
        return node['id'], node['model']
    _, model = visit([None] * n, None)
    return {'sat': model is not None, 'model': model, 'trace': trace}


def members(mask, m):
    return [i for i in range(m) if mask & (1 << i)]


def minimal_hitters(family, m):
    hits = [all(mask & f for f in family) for mask in range(1 << m)]
    return [mask for mask in range(1 << m) if hits[mask] and all(not hits[mask ^ (1 << i)] for i in members(mask, m))]


def audit(raw):
    p = validate(raw)
    n, m = p['variables'], len(p['soft'])
    all_mask = (1 << m) - 1
    cs = records(p)
    hard = cs[:len(p['hard'])]
    soft = cs[len(p['hard']):]
    truth = []
    for mask in range(1 << n):
        bits = [(mask >> i) & 1 for i in range(n)]
        values = [any(bits[abs(l)-1] == int(l > 0) for l in c['literals']) for c in cs]
        truth.append({'mask': mask, 'bits': bits, 'clause_values': values, 'hard_ok': all(values[:len(hard)]), 'soft_satisfied': [i for i, v in enumerate(values[len(hard):]) if v]})
    subsets = []
    for mask in range(1 << m):
        kept = members(mask, m)
        removed = members(all_mask ^ mask, m)
        models = [t['mask'] for t in truth if t['hard_ok'] and all(i in t['soft_satisfied'] for i in kept)]
        solve = dpll(n, hard + [soft[i] for i in kept])
        if solve['sat'] != bool(models) or (solve['model'] is not None and solve['model'] not in models):
            raise AssertionError('DPLL disagrees with full truth-table reference')
        subsets.append({'mask': mask, 'kept': kept, 'removed': removed, 'removal_cost': str(sum((Q(p['soft'][i]['cost']) for i in removed), Q(0))), 'sat': bool(models), 'models': models, 'dpll': solve})
    mus_masks = [r['mask'] for r in subsets if not r['sat'] and all(subsets[r['mask'] ^ (1 << i)]['sat'] for i in r['kept'])]
    mcs_masks = [removed for removed in range(1 << m) if subsets[all_mask ^ removed]['sat'] and all(not subsets[(all_mask ^ removed) | (1 << i)]['sat'] for i in members(removed, m))]
    mus = [{'mask': mask, 'clauses': members(mask, m), 'delete_witnesses': [{'clause': i, 'subset_mask': mask ^ (1 << i), 'models': subsets[mask ^ (1 << i)]['models']} for i in members(mask, m)]} for mask in mus_masks]
    mcs = []
    for mask in mcs_masks:
        row = subsets[all_mask ^ mask]
        mcs.append({'mask': mask, 'removed': members(mask, m), 'kept_mask': all_mask ^ mask, 'cost': row['removal_cost'], 'models': row['models'], 'reinsert_witnesses': [{'clause': i, 'subset_mask': (all_mask ^ mask) | (1 << i), 'sat': False} for i in members(mask, m)], 'unique_hit_witnesses': [{'clause': i, 'mus_mask': next(f for f in mus_masks if (f & mask) == (1 << i))} for i in members(mask, m)]})
    hit_mus = minimal_hitters(mus_masks, m)
    hit_mcs = minimal_hitters(mcs_masks, m)
    if hit_mus != mcs_masks or hit_mcs != mus_masks:
        raise AssertionError('hitting-set duality mismatch')
    dual = [{'mask': mask, 'members': members(mask, m), 'mus_intersections': [mask & f for f in mus_masks], 'mcs_intersections': [mask & f for f in mcs_masks], 'hits_all_mus': all(mask & f for f in mus_masks), 'hits_all_mcs': all(mask & f for f in mcs_masks), 'minimal_mus_hitter': mask in hit_mus, 'minimal_mcs_hitter': mask in hit_mcs} for mask in range(1 << m)]
    minimum_cardinality = min((len(c['removed']) for c in mcs), default=None)
    minimum_cost = min((Q(c['cost']) for c in mcs), default=None)
    deletion = []
    for order in [list(range(m)), list(reversed(range(m)))]:
        current = all_mask
        steps = []
        if not subsets[current]['sat']:
            for i in order:
                trial = current & ~(1 << i)
                accepted = not subsets[trial]['sat']
                steps.append({'clause': i, 'before': current, 'trial': trial, 'trial_sat': subsets[trial]['sat'], 'delete': accepted})
                if accepted:
                    current = trial
            result = current
        else:
            result = None
        deletion.append({'order': order, 'steps': steps, 'mus_mask': result})
    return {'schema': 'diagnoselab/1', 'input': p, 'clauses': cs, 'truth_table': truth, 'subsets': subsets, 'mus': mus, 'mcs': mcs, 'duality': dual, 'selection': {'minimum_cardinality': minimum_cardinality, 'cardinality_masks': [c['mask'] for c in mcs if len(c['removed']) == minimum_cardinality], 'minimum_cost': str(minimum_cost) if minimum_cost is not None else None, 'cost_masks': [c['mask'] for c in mcs if minimum_cost is not None and Q(c['cost']) == minimum_cost]}, 'deletion_runs': deletion, 'checks': {'hard_satisfiable': subsets[0]['sat'], 'full_satisfiable': subsets[all_mask]['sat'], 'dpll_truth_agree': True, 'bidirectional_duality': True, 'subsets': len(subsets), 'truth_assignments': len(truth), 'dpll_nodes': sum(len(r['dpll']['trace']) for r in subsets)}}
