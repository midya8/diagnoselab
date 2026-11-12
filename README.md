# Diagnoselab

Diagnoselab finds which removable clauses restore consistency to a small propositional formula. Supply fixed hard CNF clauses, removable soft clauses and positive rational removal costs. It lists every relative minimal unsatisfiable subset (MUS), every minimal correction set (MCS), their hitting-set relationship and the DPLL search for every soft subset. A separate exhaustive truth table checks each result.

- [Consistency inspector](https://midya8.github.io/diagnoselab/): inspect conflicts, minimal repairs, costs and search traces. See [METHOD.md](METHOD.md).
- [Consequence inspector](https://midya8.github.io/diagnoselab/consequences.html): ask whether a query clause holds under every or some model of every or some selected repair. See [CONSEQUENCES.md](CONSEQUENCES.md).

Python and independent BigInt JavaScript implementations use exact arithmetic and have no runtime dependencies.

The default control has two repairs: remove one clause at cost 5, or two clauses at total cost 2. Both are inclusion-minimal. The smallest repair is not the cheapest repair. Another retained control has disjoint cores: repairing only one does not repair the formula. Forward/reverse deletion can find different-sized minimal cores. An inconsistent hard background has no soft repair, represented explicitly by the empty relative core.

## Run locally

```sh
python -m pip install .
diagnoselab examples/demo.json --output /tmp/report.json
python -m diagnoselab examples/demo.json
python -m unittest discover -s tests -v
PYTHONPATH=. python tools/build_audits.py
PYTHONPATH=. python tools/build_consequences.py
npm test
sh tools/wheel_smoke.sh
python -m http.server 8000 --directory docs
```

The package and command line need Python 3.10+ and no runtime dependencies. Node 22+ and Chrome are needed for browser tests; uv is used only for the isolated installed-wheel check. The demo is static and computes edits locally after loading the original controls. No paid service, model API or external dataset.

## What the consistency inspector shows

- All 2^m soft subsets, complete truth-table model lists and exact removal costs.
- Complete deterministic DPLL/unit-propagation trace for every subset: initial/final partial assignments, reason clause for each forced literal, residual clauses, satisfied clause IDs, false/true branches, conflict clause and returned model.
- All relative MUSes, with satisfying model witnesses after each member deletion.
- All MCSes, with models of the remaining formula, UNSAT subset references after each reinsertion and a core uniquely hit by each removed member.
- Both directions of minimal hitting-set duality, including every candidate's intersections with every family member.
- All minimum-cardinality and minimum-cost repairs, exact rational ties and two complete deletion-order runs.
- Original/normalized clause literals and separate duplicate identities; empty/tautological clauses and fixed-background failures stay explicit.

The original consistency workflow has 17 Python tests, retained in the current suite of 24. The CI matrix covers Python 3.10-3.13. These tests include 180 independent powerset family controls, 80 complete-trace control systems, literal/variable/cost/permutation controls, all retained minimality/unique-hit witnesses, parser/no-mutation checks and CLI output preservation. These control counts are not test-function counts. Four original Node/Chrome tests, retained in the current suite of eight, compare 18 complete native/BigInt reports on 74,292 exact scalar leaves and check 90 further independent truth-mask systems. Actual Chrome checks all 827 subset outcomes, 1,301 full search-node records, 20 cores, 52 repairs, 304 truth rows, every rendered family/duality/subset table, stale/invalid clearing, export and 320/390/1280 containment. The wheel check reproduces all 18 consistency reports outside the checkout, checks the four original module origins and compares installed console/module CLIs. It also checks the consequence extension described below, for five module origins in total.

## Boundaries

At most six Boolean variables, eight hard clauses and eight removable clauses; at most 12 literal occurrences per clause. All subsets and assignments are enumerated. This is established DPLL and MUS/MCS theory, not a novel or scalable SAT/MaxSAT solver. No clause learning, external solver, performance benchmark, learned fault diagnosis, physical causal inference, DRAT/LRAT proof export or machine-checked correctness claim. Costs are supplied removal preferences, not probabilities. Restoring consistency is not evidence that the supplied clauses are true or that a real action is safe.

Native JSON and browser JSON.parse differ on duplicate keys, UTF-8 bytes versus characters and lexical float integer tokens; see the method. Original implementation, independent checks and synthetic controls: Midya Rahmani. Theory is attributed below; no external solver code or data is copied.

## Repair-policy consequences

[Consequence inspector](https://midya8.github.io/diagnoselab/consequences.html) · [Consequence method/sources](CONSEQUENCES.md)

Ask whether one query clause is true in every versus some model, under every versus some selected repair. Compare all-minimal, minimum-cost and minimum-cardinality families with all ties retained. Full countermodels and negated-query DPLL traces check entailment; a shared-clause intersection baseline is kept distinct. Strict controls separate quantifiers and show policy reversal. Empty repair families are inapplicable, not vacuous certainty.

This extension brings the total to 24 Python test functions and eight Node/Chrome tests while retaining the original tests above. 26 complete consequence reports compare on 16,165 exact scalar leaves: 67 repairs, 78 policy records and 151 negated-query nodes including intersection baselines. Actual Chrome verifies 78 complete policy records, 67 repairs, 70 selected per-repair nodes, 462 literal rows, all tables, export and stale/invalid clearing. The installed wheel reproduces all 18 base and 26 consequence reports outside the checkout with five module origins. No database/description-logic engine, probabilities or real-world truth claim.

```sh
python -m diagnoselab.consequences examples/demo.json --query '[1]' --output /tmp/consequences.json
```
