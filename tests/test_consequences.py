import copy
import json
import random
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from diagnoselab.consequences import consequences
from tools.build_consequences import controls
from tools.build_audits import make
from test_core import models, powers, check_trace


def holds(model, query):
    return any(bool(model & 2**(abs(l)-1)) == (l > 0) for l in query)


class ConsequenceTests(unittest.TestCase):
    def verify(self, p, q, r):
        m = len(p['soft']); universe = set(range(m)); sets = powers(m)
        correct = {frozenset(s): models(p, universe-s) for s in sets}
        repairs = [s for s in sets if correct[frozenset(s)] and not any(correct[frozenset(t)] for t in sets if t < s)]
        self.assertEqual([set(x['removed']) for x in r['repairs']], repairs)
        by_mask = {x['removed_mask']: x for x in r['repairs']}
        for row in r['repairs'] + [x['intersection_baseline'] for x in r['policies'] if x['intersection_baseline'] is not None]:
            expected = models(p, [i for i in range(m) if row['kept_mask'] & 2**i])
            self.assertEqual(row['models'], expected)
            self.assertEqual(row['query_true_models'], [v for v in expected if holds(v,q)])
            self.assertEqual(row['countermodels'], [v for v in expected if not holds(v,q)])
            self.assertEqual(row['entailed'], all(holds(v,q) for v in expected))
            self.assertEqual(row['possible'], any(holds(v,q) for v in expected))
            self.assertEqual(row['negated_query_dpll']['sat'], bool(row['countermodels']))
            cs = [(c['id'], c['literals']) for c in row['negated_query_clauses']]
            check_trace(self, p, {'dpll': row['negated_query_dpll']}, clauses=cs)
        all_masks = [sum(2**i for i in s) for s in repairs]
        cost = lambda mask: sum((Fraction(p['soft'][i]['cost']) for i in range(m) if mask & 2**i), Fraction(0))
        expected_policies = [all_masks, [v for v in all_masks if cost(v)==min(map(cost,all_masks))] if all_masks else [], [v for v in all_masks if v.bit_count()==min(x.bit_count() for x in all_masks)] if all_masks else []]
        for policy, masks in zip(r['policies'], expected_policies):
            self.assertEqual(policy['repair_masks'], masks)
            rows = [by_mask[v] for v in masks]
            union = sorted({v for row in rows for v in row['models']})
            self.assertEqual(policy['models_union'], union)
            for key, f, g in [('entailed_every_repair',all,all),('entailed_some_repair',any,all),('possible_every_repair',all,any),('possible_some_repair',any,any)]:
                self.assertEqual(policy[key], f(g(holds(v,q) for v in row['models']) for row in rows) if rows else None)
            for lit in policy['literal_consequences']:
                self.assertEqual(lit['all_models'], all(holds(v,[lit['literal']]) for v in union) if rows else None)
                self.assertEqual(lit['some_model'], any(holds(v,[lit['literal']]) for v in union) if rows else None)
            if rows:
                self.assertEqual(policy['kept_in_every_repair'], ((1<<m)-1) ^ policy['removed_in_some_repair'])
                self.assertTrue(set(union) <= set(policy['intersection_baseline']['models']))
            else:
                self.assertIsNone(policy['intersection_baseline'])
                self.assertIsNone(policy['removed_in_every_repair'])

    def test_all_26_retained_complete_consequences_and_trace_replay(self):
        saved = json.loads((Path(__file__).parents[1]/'docs/consequences-audits.json').read_text())
        for (name,p,q), row in zip(controls(), saved):
            r=consequences(p,q);self.assertEqual(row['report'],r,name);self.verify(p,q,r)
        self.assertEqual(len(saved),26)

    def test_90_independent_all_proper_subset_query_oracles(self):
        rng=random.Random(431)
        for _ in range(90):
            n=rng.randint(1,4)
            clause=lambda:[rng.choice([-1,1])*rng.randint(1,n) for _ in range(rng.randint(0,3))]
            p=make(n,[clause() for _ in range(rng.randint(0,6))],[str(rng.randint(1,4)) for _ in range(6)],hard=[clause() for _ in range(rng.randint(0,2))])
            q=clause();self.verify(p,q,consequences(p,q))

    def test_default_policy_reversal_and_free_variable_quantifier_gap(self):
        rows=controls();r=consequences(rows[0][1],rows[0][2])
        self.assertTrue(r['policies'][1]['entailed_every_repair']);self.assertFalse(r['policies'][2]['possible_some_repair'])
        r=consequences(rows[21][1],rows[21][2]);self.assertTrue(r['policies'][0]['possible_every_repair']);self.assertFalse(r['policies'][0]['entailed_some_repair'])

    def test_intersection_entailment_chain_can_be_strict(self):
        for _,p,q in controls()[22:24]:
            r=consequences(p,q)
            for policy in r['policies']:
                self.assertTrue(policy['entailed_every_repair']);self.assertFalse(policy['intersection_baseline']['entailed'])
                self.assertIn(0,policy['intersection_baseline']['countermodels']);self.assertNotIn(0,policy['models_union'])

    def test_tautology_empty_query_and_no_repairs(self):
        p=make(2,[[1],[-1]])
        for q,value in [([],False),([2,-2],True)]:
            r=consequences(p,q);self.assertTrue(all(row['entailed']==value and row['possible']==value for row in r['repairs']))
        r=consequences(make(2,[[1]],hard=[[]]),[1])
        self.assertEqual(r['repairs'],[]);self.assertTrue(all(x['entailed_every_repair'] is None for x in r['policies']))

    def test_query_validation_no_mutation_and_literal_equivalence(self):
        p=controls()[0][1];q=[1];before=copy.deepcopy((p,q));a=consequences(p,q);self.assertEqual((p,q),before)
        for bad in [None,{},'x',[0],[True],[1.0],[7],[1]*13]:
            with self.assertRaises(ValueError):consequences(p,bad)
        b=consequences(p,[1,1]);self.assertEqual([r['countermodels'] for r in a['repairs']],[r['countermodels'] for r in b['repairs']])
        c=copy.deepcopy(p)
        for s in c['soft']:s['cost']=str(7*Fraction(s['cost']))
        self.assertEqual([r['repair_masks'] for r in a['policies']],[r['repair_masks'] for r in consequences(c,q)['policies']])

    def test_module_cli_and_invalid_output_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json';out=Path(d)/'out.json';p.write_text(json.dumps(controls()[0][1]));out.write_text('preserved')
            call=lambda q:subprocess.run([sys.executable,'-m','diagnoselab.consequences',str(p),'--query',q,'--output',str(out)],capture_output=True,text=True)
            self.assertEqual(call('[0]').returncode,2);self.assertEqual(out.read_text(),'preserved');self.assertEqual(call('[1]').returncode,0);self.assertEqual(json.loads(out.read_text()),consequences(controls()[0][1],[1]))
