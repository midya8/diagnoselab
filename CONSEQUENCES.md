# Repair-policy consequences: method and boundaries

[Live consequence inspector](https://midya8.github.io/diagnoselab/consequences.html) · [Base conflicts and repairs](README.md) · [Base method and seven theory sources](METHOD.md)

## Question and exact semantics

Given hard clauses H, soft clause identities S and positive rational removal costs, enumerate the same complete minimal correction sets R as the base inspector. Each repaired formula is H AND (S minus R), always satisfiable. A query is one disjunctive clause of up to 12 signed literals in the declared six-variable domain. Empty query [] is false, tautological query is true, duplicate query literals keep the same meaning. Query-negation clauses are temporary checks, never removable source clauses.

For a nonempty selected repair family P, distinguish all four quantifiers:

- `entailed_every_repair`: for every R in P, every model of its repaired formula satisfies q.
- `entailed_some_repair`: there exists R in P such that every model of its repaired formula satisfies q.
- `possible_every_repair`: for every R in P, there exists a model of its repaired formula satisfying q.
- `possible_some_repair`: there exists R in P and a model of its repaired formula satisfying q.

A query merely possible in a repair is not necessarily entailed by that repair. The free-variable control has `possible_every_repair=true` and `entailed_some_repair=false`. No quantifier is silently substituted for another.

Policies are all inclusion-minimal repairs, every tied minimum-cost repair, and every tied minimum-cardinality repair. Costs use the existing exact Fraction/BigInt arithmetic. Default q=x1 is entailed under minimum cost and impossible under minimum cardinality. This is a policy contrast, not proof one policy is correct. All ties are retained. An inconsistent hard background has no repair: policies are explicitly inapplicable, query/literal booleans null, not vacuous certainty. This is a deliberate product convention rather than classical universal quantification over the empty set.

## Countermodels, traces and intersection baseline

Each repair retains all complete models, the full query-true model list and full countermodel list. For q=(l1 OR ... OR lk), negate q by appending the k unit clauses NOT l1 through NOT lk, labelled q0, q1, ... . Run the original deterministic DPLL engine on the repaired formula plus those units. SAT must agree exactly with the existence of a truth-table countermodel; its returned model must belong to that list. UNSAT means the consistent repaired formula entails q. Every complete search node, unit reason, residual state, branch, conflict and returned model remains in the report. Empty query appends no units; tautological query appends contradictory units. Original clauses keep their h/s identities.

For each policy, also intersect the kept soft identities and query H plus that intersection. This baseline is not the intersection of models or query answers. Its model set contains the union of the selected repairs' models and can contain extra models absent from every repair. For a nonempty family, intersection-baseline entailment implies every-repair entailment, which implies some-repair entailment. We check this chain but do not infer equivalence. Two- and three-way original controls make the first implication strict: every repair entails a disjunction, but the shared-clause baseline admits the all-false countermodel. Model union, membership consensus and all literal true/counterexample witnesses are retained separately.

Literal `all_models`/`some_model` fields range over the union of complete models of the selected repair family. Every literal has a first witness/countermodel where available. Removal masks common to every/some repair and kept identities common to every repair are exact bitset intersections/unions. A model mask's bit i is variable x(i+1); a repair mask's bit i is soft identity si. These are distinct spaces. Counts are not probabilities.

## Reproduction and checks

```sh
python -m pip install .
python -m diagnoselab.consequences examples/demo.json --query '[1]' --output /tmp/consequences.json
python -m unittest discover -s tests -v
PYTHONPATH=. python tools/build_consequences.py
npm test
sh tools/wheel_smoke.sh
python -m http.server 8000 --directory docs
```

24 Python test functions run on 3.10-3.13, retaining all 17 base tests and adding seven consequence tests. New checks independently enumerate every proper-subset repair candidate and model, replay every temporary query-negation trace, and add 90 seeded query systems, empty/tautological/duplicate queries, no-repair null semantics, cost scaling, no mutation, strict quantifier gaps, intersection countermodels and invalid CLI output preservation. A shared trace replay helper accepts explicit clause IDs; its original default and all base tests remain.

Eight Node/actual-Chrome tests retain all four originals and add four consequence tests. Independent Python/BigInt consequence reports compare exactly on 16,165 scalar leaves across 26 original controls, with 90 further independent brute-force query/repair controls. The 26 reports contain 67 repaired formulas, 78 policy records and 151 query-negation search nodes including policy-intersection baselines. Actual Chrome checks all 78 policy records, 67 repair records, 70 explicitly selectable per-repair nodes, 462 literal table rows, every policy/repair/clause/trace table, full JSON records, export and invalid/stale clearing at 320/390/1280. Policy-intersection traces are retained in the complete policy JSON and replayed natively. Control/system counts are not test-function counts or benchmarks. Added controls force both UNSAT two-branch refutation and satisfiable branching, not only unit propagation.

The installed wheel reproduces all 18 base and 26 consequence reports outside the checkout, verifies five module origins and runs the new module CLI. CI regenerates both fixture files and retains the original fixture comparison. Browser query text is bounded to 1024 characters before JSON.parse; the native CLI validates the resulting at-most-12-literal structure without the same text-length cap. Other native/browser parsing differences remain in METHOD.md.

## Sources and exact adaptation

The base DPLL/MUS/MCS sources remain attributed in METHOD.md. These additional sources were inspected for consequence semantics, not copied as implementation, examples, datasets or performance results:

1. Meghyn Bienvenu, Camille Bourgaux and Francois Goasdoue, *Explaining Inconsistency-Tolerant Query Answering over Description Logic Knowledge Bases*, AAAI2016 extended paper. Introduction/preliminaries inspected for every-repair, some-repair and intersection-of-repairs entailment, with entailment itself universally quantified over models: https://www.labri.fr/perso/meghyn/papers/BieBouGoa-AAAI16-long.pdf . We implement a finite propositional clause-query analogue, not their DL-Lite/CQ framework, minimal explanation/cause algorithms, CQAPri, SAT4J or LUBM experiments.
2. Meghyn Bienvenu, *Inconsistency Handling in Ontology-Mediated Query Answering: A Progress Report*, CEUR invited paper. Definitions1-4 and discussion of preferred repair families inspected: https://ceur-ws.org/Vol-2373/invited-2.pdf . AR/IAR/brave are formal names in that ontology setting; our explicit quantifier field names avoid claiming the entire formalism or all its properties.
3. Meghyn Bienvenu, *KR Meets Data Quality*, KR2024 keynote. Querying inconsistent data and repair-based/preferred semantics inspected: https://kr.org/KR2024/kr-keynote-data-quality-meghyn.pdf . We do not implement database constraints, ontology-mediated queries, priorities or the cited cost-based knowledge-base systems.
4. Armin Biere and Martina Seidl, JKU *Logic: Propositional Reasoning*, WS2018/2019, version2019.1. SAT reduction and entailment sections inspected for F entails q iff F AND NOT q is UNSAT, and the DPLL/BCP sections for context: https://fmv.jku.at/logic/ws19/logic-SAT-checking.pdf . No lecture implementation copied; no resolution proof format added.

## Limits

Six Boolean variables, at most eight hard and eight removable clauses; exhaustive subset/model enumeration. This is established propositional reasoning with independently tested computational witnesses. No scalable SAT, MaxSAT, database or description-logic engine, novel complexity result, calibrated probability, real fault/causal diagnosis, DRAT/LRAT export or machine-checked correctness claim. All certainty is conditional on supplied clauses and the policy, not evidence those clauses are true. No paid API, model or private data. Original implementation, checks and synthetic controls: Midya Rahmani.
