import copy
import itertools
import json
import random
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from diagnoselab import audit, parse
from diagnoselab.core import validate
from tools.build_audits import cases, make


def models(p, kept):
    out = []
    for bits in itertools.product([0, 1], repeat=p['variables']):
        clauses = p['hard'] + [p['soft'][i]['clause'] for i in kept]
        if all(any(bool(bits[abs(l)-1]) == (l > 0) for l in c) for c in clauses):
            out.append(sum(v * 2**i for i, v in enumerate(bits)))
    return sorted(out)


def powers(m):
    return [set(i for i in range(m) if mask & 2**i) for mask in range(2**m)]


def check_trace(test, p, row):
    clauses = [('h'+str(i), c) for i, c in enumerate(p['hard'])] + [('s'+str(i), p['soft'][i]['clause']) for i in row['kept']]
    trace = row['dpll']['trace']
    seen = set()
    def active(a):
        remaining, satisfied = [], []
        for cid, raw in clauses:
            c = sorted(set(raw), key=lambda l: (abs(l), l))
            if any(-l in c for l in c) or any(a[abs(l)-1] is not None and bool(a[abs(l)-1]) == (l > 0) for l in c):
                satisfied.append(cid)
            else:
                remaining.append({'id': cid, 'literals': [l for l in c if a[abs(l)-1] is None]})
        return remaining, satisfied
    def visit(index, expected, parent):
        test.assertNotIn(index, seen); seen.add(index)
        t = trace[index]
        test.assertEqual((t['id'], t['parent'], t['initial']), (index, parent, expected))
        a = list(expected)
        for step in t['steps']:
            rest, _ = active(a)
            test.assertFalse(any(not c['literals'] for c in rest))
            units = [c for c in rest if len(c['literals']) == 1]
            test.assertTrue(units)
            unit = units[0]
            test.assertEqual((step['clause_id'], step['literal']), (unit['id'], unit['literals'][0]))
            l = step['literal']; test.assertIsNone(a[abs(l)-1]); a[abs(l)-1] = int(l > 0)
            test.assertEqual(a, step['assignment_after'])
        rest, sat = active(a)
        test.assertEqual((t['assignment'], t['residual'], t['satisfied_ids']), (a, rest, sat))
        if t['kind'] == 'conflict':
            test.assertEqual(t['conflict_clause'], next(c['id'] for c in rest if not c['literals']))
            test.assertEqual(t['children'], []);test.assertIsNone(t['model'])
        elif t['kind'] == 'model':
            test.assertEqual(rest, []); test.assertEqual(t['model'], sum((v or 0)*2**i for i,v in enumerate(a)))
            test.assertEqual(t['children'], [])
        else:
            test.assertEqual(t['kind'], 'split')
            test.assertTrue(all(len(c['literals']) > 1 for c in rest))
            var = min(abs(l) for c in rest for l in c['literals'])-1
            test.assertEqual(t['split_variable'], var); test.assertIn(len(t['children']), [1, 2])
            for bit, child in enumerate(t['children']):
                a2 = list(a); a2[var] = bit; visit(child, a2, index)
            first = trace[t['children'][0]]['model']
            if first is not None:
                test.assertEqual(len(t['children']), 1); test.assertEqual(t['model'], first)
            else:
                test.assertEqual(len(t['children']), 2); test.assertEqual(t['model'], trace[t['children'][1]]['model'])
    visit(0, [None]*p['variables'], None)
    test.assertEqual(seen, set(range(len(trace))))
    test.assertEqual((row['dpll']['sat'], row['dpll']['model']), (trace[0]['model'] is not None, trace[0]['model']))


class DiagnosisTests(unittest.TestCase):
    def test_retained_controls_and_all_dpll_nodes(self):
        for name,p in cases():
            r = audit(p)
            for row in r['subsets']:
                self.assertEqual(row['models'], models(p, row['kept']), name)
                check_trace(self, p, row)

    def test_180_independent_powerset_family_oracles(self):
        rng = random.Random(154)
        for _ in range(180):
            n = rng.randint(1, 5); m = rng.randint(0, 7)
            c = lambda: [rng.choice([-1, 1])*rng.randint(1,n) for _ in range(rng.randint(0,4))]
            p = make(n, [c() for _ in range(m)], hard=[c() for _ in range(rng.randint(0,3))])
            r = audit(p); sets = powers(m); universe = set(range(m))
            sat = {frozenset(s): bool(models(p,s)) for s in sets}
            mus = [s for s in sets if not sat[frozenset(s)] and all(sat[frozenset(t)] for t in sets if t < s)]
            mcs = [s for s in sets if sat[frozenset(universe-s)] and all(not sat[frozenset(universe-t)] for t in sets if t < s)]
            self.assertEqual([set(x['clauses']) for x in r['mus']], mus)
            self.assertEqual([set(x['removed']) for x in r['mcs']], mcs)

    def test_80_trace_oracles_with_conflict_branching(self):
        rng = random.Random(551)
        for _ in range(80):
            n = rng.randint(1, 6)
            p = make(n, [[rng.choice([-1,1])*v for v in rng.sample(range(1,n+1),rng.randint(1,min(n,3)))] for _ in range(6)])
            r = audit(p)
            for row in r['subsets']:
                check_trace(self,p,row)

    def test_default_cost_and_cardinality_are_different(self):
        r=audit(cases()[0][1]);self.assertEqual([x['mask'] for x in r['mcs']],[1,6]);self.assertEqual(r['selection'],{'minimum_cardinality':1,'cardinality_masks':[1],'minimum_cost':'2','cost_masks':[6]})

    def test_hard_inconsistency_and_empty_relative_core(self):
        r=audit(make(1,[[1]],hard=[[]]));self.assertEqual(r['mus'],[{'mask':0,'clauses':[],'delete_witnesses':[]}]);self.assertEqual(r['mcs'],[]);self.assertIsNone(r['selection']['minimum_cost']);self.assertFalse(any(d['hits_all_mus'] for d in r['duality']))

    def test_satisfiable_empty_and_unused_variables(self):
        r=audit(make(6,[]));self.assertEqual(r['mus'],[]);self.assertEqual([x['mask'] for x in r['mcs']],[0]);self.assertEqual(r['subsets'][0]['models'],list(range(64)));self.assertEqual(r['subsets'][0]['dpll']['model'],0)

    def test_single_core_does_not_repair_disjoint_core(self):
        r=audit(cases()[1][1]);self.assertEqual([x['mask'] for x in r['mus']],[3,12]);self.assertFalse(r['subsets'][15^1]['sat']);self.assertEqual(r['selection']['minimum_cardinality'],2)

    def test_minimal_not_minimum_core_and_deletion_order(self):
        r=audit(cases()[9][1]);self.assertEqual([x['mus_mask'] for x in r['deletion_runs']],[28,3]);self.assertEqual([len(x['clauses']) for x in r['mus']],[2,3])

    def test_all_family_minimality_and_unique_hit_witnesses(self):
        for _,p in cases():
            r=audit(p)
            for core in r['mus']:
                for w in core['delete_witnesses']:
                    self.assertTrue(w['models']);self.assertEqual(w['models'],r['subsets'][w['subset_mask']]['models'])
            for c in r['mcs']:
                self.assertTrue(c['models'])
                for w in c['reinsert_witnesses']:self.assertFalse(r['subsets'][w['subset_mask']]['sat'])
                for w in c['unique_hit_witnesses']:self.assertEqual(w['mus_mask']&c['mask'],2**w['clause'])

    def test_positive_cost_scaling_and_soft_permutation(self):
        for _,p in cases():
            r=audit(p);q=copy.deepcopy(p)
            for s in q['soft']:s['cost']=str(3*Fraction(s['cost']))
            scaled=audit(q);self.assertEqual(scaled['selection']['cost_masks'],r['selection']['cost_masks'])
            if r['selection']['minimum_cost'] is not None:self.assertEqual(Fraction(scaled['selection']['minimum_cost']),3*Fraction(r['selection']['minimum_cost']))
            q=copy.deepcopy(p);q['soft'].reverse();other=audit(q);m=len(p['soft']);reverse=lambda mask:sum(2**(m-1-i) for i in range(m) if mask&2**i)
            self.assertEqual(sorted(reverse(c['mask']) for c in r['mus']),[c['mask'] for c in other['mus']]);self.assertEqual(sorted(reverse(c['mask']) for c in r['mcs']),[c['mask'] for c in other['mcs']])

    def test_literal_permutation_duplication_and_variable_complement(self):
        for _,p in cases():
            r=audit(p);q=copy.deepcopy(p)
            q['hard']=[[-l for l in reversed(c+c)] for c in p['hard']]
            for s in q['soft']:s['clause']=[-l for l in reversed(s['clause']+s['clause'])]
            # Duplication can exceed the input cap only in externally generated data; these controls do not.
            other=audit(q)
            self.assertEqual([c['mask'] for c in r['mus']],[c['mask'] for c in other['mus']]);self.assertEqual([c['mask'] for c in r['mcs']],[c['mask'] for c in other['mcs']])
            for row,alt in zip(r['subsets'],other['subsets']):self.assertEqual(sorted(((1<<p['variables'])-1)^v for v in row['models']),alt['models'])

    def test_duplicate_clauses_have_distinct_removal_identity(self):
        r=audit(make(1,[[1],[-1],[-1]],['5','1','1']));self.assertEqual([x['mask'] for x in r['mcs']],[1,6]);self.assertEqual(r['clauses'][1]['normalized'],r['clauses'][2]['normalized'])

    def test_empty_clause_tautology_repeated_literal(self):
        r=audit(make(2,[[],[1,-1],[2,2]]));self.assertEqual([c['mask'] for c in r['mus']],[1]);self.assertEqual([c['mask'] for c in r['mcs']],[1]);self.assertTrue(r['clauses'][1]['tautology']);self.assertEqual(r['clauses'][2]['normalized'],[2])

    def test_validation_and_no_mutation(self):
        p=cases()[0][1];before=copy.deepcopy(p);audit(p);self.assertEqual(p,before)
        bad=[{},make(0,[]),make(True,[]),make(7,[]),make(1,[[0]]),make(1,[[2]]),make(1,[[True]]),make(1,[[1.0]]),make(1,[[1]*13]),make(1,[[1]]*9),make(1,[],hard=[[1]]*9)]
        for cost in ['0','-1','nan','1/0','01','1e1','10001','1/1000000',1,True]:bad.append({'variables':1,'hard':[],'soft':[{'clause':[1],'cost':cost}]})
        bad.append({'variables':1,'hard':[],'soft':[{'clause':[1],'cost':'1','extra':1}]})
        for x in bad:
            with self.assertRaises(ValueError,msg=str(x)):audit(x)

    def test_native_json_rejects_duplicate_nonfinite_and_bounds(self):
        for s in ['{"variables":1,"variables":2,"hard":[],"soft":[]}','{"variables":NaN,"hard":[],"soft":[]}',' '*32769,'{"variables":1.0,"hard":[],"soft":[]}']:
            with self.assertRaises(ValueError):parse(s)
        self.assertEqual(parse(json.dumps(make(1,[]))),make(1,[]))

    def test_saved_reports_exact(self):
        rows=json.loads((Path(__file__).resolve().parents[1]/'docs/audits.json').read_text())
        self.assertEqual(len(rows),18)
        for x in rows:self.assertEqual(audit(x['input']),x['report'])

    def test_cli_and_invalid_output_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'input.json';out=Path(d)/'out.json';src.write_text(json.dumps(cases()[0][1]))
            p=subprocess.run([sys.executable,'-m','diagnoselab',str(src),'--output',str(out)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(out.read_text()),audit(cases()[0][1]));before=out.read_bytes();src.write_text('{}');p=subprocess.run([sys.executable,'-m','diagnoselab',str(src),'--output',str(out)],capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertEqual(out.read_bytes(),before)


if __name__=='__main__':unittest.main()
