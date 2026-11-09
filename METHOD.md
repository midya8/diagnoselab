# Diagnoselab method, witnesses and limits

[Live inspector](https://midya8.github.io/diagnoselab/) · [README](README.md)

## Exact finite question

A clause is a disjunction of signed integer literals; literal 1 is x1 and -1 is its negation. Hard clauses H are always present. Each soft clause si has its own identity and positive rational removal cost wi. For every subset K of soft identities, decide SAT(H AND K) and retain every satisfying complete assignment in a separate truth-table reference. A subset mask uses bit i for si. A model mask uses bit i for x(i+1); these are different spaces.

Input requires exactly `variables`, `hard` and `soft`. Variables is an integer 1..6, hard and soft have at most eight entries each, and each clause has at most 12 literal occurrences, each a nonzero integer in [-n,n]. A soft entry has exactly `clause` and `cost`. A cost is a positive rational string <=10000; numerator has at most six digits (optional minus is parsed but nonpositive values rejected), denominator is a positive at-most-six-digit integer, no leading zero except integer zero, no decimal or exponent. Costs normalize as exact fractions. Total costs and comparisons use Fraction in Python and BigInt rational pairs in JavaScript, never floating point.

Within a clause, repeated literals normalize to one occurrence, sorted by absolute variable then sign. A clause containing both signs of a variable is a tautology. Original literals remain in the report. Distinct input clauses remain distinct identities even when their logical content is identical. Empty clause is false; empty conjunction is true. Unused variables remain in the declared domain and therefore multiply complete truth-table model counts.

Native parse bounds 32,768 UTF-8 bytes, rejects duplicate keys/nonfinite numbers and requires actual JSON integer tokens for variables/literals. Browser JSON.parse bounds 32,768 characters, keeps the last duplicate key and accepts lexical 1.0 as integer 1. These parser differences are disclosed, not claimed equivalent. Direct audit calls validate bounded structure but do not impose a serialized-byte limit. No input object is mutated.

## DPLL trace and independent reference

Start a partial assignment with every variable unassigned. For each clause, either record it satisfied, or remove literals falsified by the partial assignment. Tautologies are always satisfied. A residual empty clause is a conflict. Otherwise propagate the first residual unit in clause order, retaining its clause ID, literal and resulting partial assignment. Repeat until conflict, all clauses satisfied, or no unit remains.

When branching is needed, take the lowest-index variable among unresolved literals, try false then true, and stop after the first successful child. Each node retains its initial/final assignment, all propagation reasons, residual clauses, satisfied IDs, conflict ID or split variable, child IDs and returned model. At a model node, complete unassigned bits with zero. This is satisfiability search, not a model-counting trace; unexplored branches after success are not claimed exhausted. An UNSAT node must be a conflict or have both children UNSAT. The implementation has no pure-literal rule, watched literals, learning, restarts or industrial preprocessing.

Separately enumerate all 2^n complete assignments and evaluate the original, unnormalized literal lists directly. Each subset's full model list must agree with the DPLL SAT/UNSAT answer, and every returned model must occur in that list. Python tests independently replay every reason, residual state, branch assignment, child closure and model completion. This is a tested computational witness, not a DRAT/LRAT export, certified checker or machine-checked proof.

## Minimal families and duality

A relative MUS U is a soft subset with H AND U UNSAT and every U minus one member SAT. By monotonicity of conjunction, single-deletion checks imply all proper subsets are SAT. If H itself is inconsistent, U is empty. Such a core is relative to H, not necessarily a minimal set of all hard and soft clauses.

An MCS R is a soft removal set with H AND (S minus R) SAT and every single reinsertion UNSAT. It is the complement of a maximal satisfiable soft subset. Single-reinsertion tests suffice by monotonicity. If the full formula is SAT, the only MCS is the empty removal and there are no MUSes. If H is UNSAT, there are no repairs and the MUS family contains the empty set.

All candidates are checked in both directions: the inclusion-minimal hitting sets of all MUSes must equal all MCSes, and vice versa. Every candidate retains every intersection. The minimal hitting set of an empty family is the empty set; a family containing the empty set has no hitting set. Those conventions retain the boundary cases above.

Each MUS member deletion has a full satisfying model list. Each MCS member reinsertion references its UNSAT subset and full DPLL trace. Each removed member additionally has a MUS whose intersection with the repair is exactly that member, a unique-hit witness to irredundancy. We enumerate all subsets directly, not via CAMUS, MARCO or an implicit hitting-set search.

Positive removal costs ensure that any minimum-cost correction is inclusion-minimal, since a nonminimal correction can remove fewer positive costs. Thus it is sufficient to select minimum costs over MCSes; every exact cost/cardinality tie is retained. Costs are preferences, not probabilities or Bayesian posteriors. Inclusion-minimal does not mean minimum cardinality, minimum cost or a unique explanation.

The two deletion runs start from the full inconsistent soft set. Each trial deletes one clause and keeps the deletion iff inconsistency remains. Satisfiability is monotone under further deletions, so a clause previously retained cannot become deletable later. This yields one relative minimal core, not all cores or a minimum-cardinality core. If the full formula is SAT, the result is null, not the empty UNSAT core.

## Original retained failures

Default: hard clause (-x1 OR x2), soft s0=x1 at cost5, s1=NOT x2 at cost1, duplicate s2=NOT x2 at cost1 and tautological s3=(x3 OR NOT x3) at cost2. MUS masks3/5 represent {s0,s1}/{s0,s2}. MCS masks1/6 represent {s0} at cost5 and {s1,s2} at cost2. Duplicate negative clauses must both be removed unless s0 is removed. The tautology never needs removal. This separates minimality, cardinality and cost.

Other controls include two disjoint conflicts, four two-variable clauses needing both DPLL branches, inconsistent hard units, empty hard and soft clauses, repeated literals, already-SAT and no-soft cases, a two-versus-three-member core chosen by deletion order, six declared variables with unused bits, a six-variable implication chain with fractional costs, and five seeded signed systems (seed9417). No benchmark data or external example is copied.

18 retained controls give 827 subset reports, 1,301 DPLL nodes, 20 relative cores, 52 minimal repairs and 304 complete truth-table rows. 17 Python test functions run on 3.10-3.13. Independent tests include 180 all-proper-subset family oracles, 80 whole-trace systems, positive cost scaling, soft permutation, literal repetition/order and variable complementation, all retained minimality and unique-hit witnesses, validation/no mutation and CLI invalid-output preservation. Four Node/Chrome tests compare all complete reports on 74,292 scalar leaves, check 90 independent truth-mask systems and every rendered record/table, export and stale/invalid behavior. Control counts are not test-function counts.

## Reproduction

```sh
python -m pip install .
diagnoselab examples/demo.json --output /tmp/diagnosis.json
python -m diagnoselab examples/demo.json
python -m unittest discover -s tests -v
PYTHONPATH=. python tools/build_audits.py
npm test
sh tools/wheel_smoke.sh
```

The isolated wheel check uses Python3.10 outside the checkout, verifies four module origins, reproduces all 18 reports and compares installed console/module output. CI runs Python3.10-3.13, deterministic fixture regeneration, Node22/Chrome and the wheel check. The static demo does not call any model or external solver. Tests and mathematical bounds are not a speed benchmark. The full method enumerates 2^m soft subsets and 2^n assignments; no large-system or complexity improvement is claimed.

## Grounded theory and implementation distinctions

1. Raymond Reiter, *A Theory of Diagnosis from First Principles*, Artificial Intelligence32 (1987),57-95. Introduction, definitions2.4/4.3, theorem4.4 and corollary4.5 inspected. Minimal diagnoses as minimal hitting sets of conflicts. We apply propositional clause-removal consistency analysis, not the full abnormal-component first-order framework or real diagnosis: https://www.cse.sc.edu/~mgv/csce580f11/gradPres/reiter-diagnosis.pdf
2. Joao Marques-Silva, Federico Heras, Mikolas Janota, Alessandro Previti and Anton Belov, *On Computing Minimal Correction Subsets*, IJCAI2013. Introduction/preliminaries inspected for MCS/MUS definitions, MaxSAT cost/cardinality distinction and duality. We do not implement their performance algorithms. The fetched text of MSS definition3 has a malformed union expression; we use the correct extension definition corroborated by the next source: https://ijcai.org/proceedings/2013/0098.pdf
3. Fahiem Bacchus and George Katsirelos, *Using Minimal Correction Sets to more Efficiently Compute Minimal Unsatisfiable Sets*, CAV2015 manuscript. Background definitions1-4 and proposition1 inspected for MUS/MCS semantics and the unique-hit witness. No source implementation or experimental result imported: https://gkatsi.github.io/papers/bkcav15.pdf
4. Mark H. Liffiton and Karem A. Sakallah, *Algorithms for Computing Minimal Unsatisfiable Subsets of Constraints*, author manuscript visibly dated October2007; a separate inspected tutorial cites the 2008 JAR publication. Introduction, definitions and section3 inspected for full-family versus single-core distinction and bidirectional hitting-set duality. We do not implement CAMUS or use its figures/data: https://markliffiton.com/publications/jar_liffiton_CAMUS.pdf
5. Anton Belov and Joao Marques-Silva, *Generalizing Redundancy in Propositional Logic: Foundations and Hitting Sets Duality*, arXiv1207.1257v2 (2012). Section2 group-0/background convention and theorem2.1 inspected. Fixed background can produce an empty relative MUS; duplicate clause identities require labelled/multiset care. We implement single-clause soft identities, not general overlapping labelled groups: https://arxiv.org/abs/1207.1257v2
6. Ruben Martins, CMU15-414 *Lecture Notes on Solving SAT with DPLL*, March19,2024, sections5-7 inspected. Exhaustive case splitting, unit propagation, DPLL and practical distinction from industrial solvers. Original implementation; no source code copied: https://www.cs.cmu.edu/~15414/s24/lectures/16-satdpll.pdf
7. Mate Soos, *Proof Traces for SAT solvers*, April12,2022. SAT witness checking, resolution/RUP and proof-format discussion inspected. Motivates the distinction between an inspectable search trace and DRAT/LRAT-style or formally verified proof checking. We implement no such proof format and make no certified claim: https://www.msoos.org/2022/04/proof-traces-for-sat-solvers/

Additional tutorial inspected only for terminology/publication context, no code reused: CPMpy IJCAI22 MUS extraction notebook https://github.com/CPMpy/cpmpy/blob/master/examples/tutorial_ijcai22/3_musx.ipynb . Its CP modeling and solver integration are not implemented here.

Original code, independent checks and synthetic controls: Midya Rahmani. Established algorithms and theory remain attributed to their authors. Consistency is not truth, supplied cost is not failure probability, and no physical, medical or causal diagnosis is established.
