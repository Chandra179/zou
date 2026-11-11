# Business rules: file format and how-to

Applies the [evaluation model](../evaluation-model.yaml) to one focused problem: specifying and checking an app's behavioral business rules. The format and [checker](../tools/business-rules/check_rules.py) are plain Python and need no Claude. The optional, Claude-installed [business-rules skill](../.claude/skills/business-rules/SKILL.md) helps draw rules out. This tool does not yet implement the broader design, resource, implementation, or runtime evaluation capabilities described by the model.

## The idea

Write every rule as a record that answers: who decided it, which concrete cases define it, how it is checked, and what the evidence says. Then a script reports what is confirmed, what is only assumed, and what is unknown. There is no overall score, because unknown is not satisfied.

## Rule record

| Field | Meaning |
| --- | --- |
| `id`, `statement` | Stable name and the rule in plain language (EARS wording is optional). |
| `status` | `confirmed`: a decision maker decided it. `proposed`: inferred, awaiting a decision. `open`: an unresolved question. |
| `revision` | Integer, starting at 1. Bump it each time a decision maker re-decides a confirmed rule, including several times on one day. |
| `required` | Rule-level acceptance gate: `true` when this outcome, invariant, or hard constraint blocks acceptance while unevidenced; `false` when it does not. Mandatory on confirmed rules. This is distinct from a scenario's `kind: required`, which means that scenario must work. |
| `source`, `decided_by`, `decided_on` | Where it came from and who decided it. Required for `confirmed`; the source cannot be `inferred`. |
| `scenarios` | Concrete given / when / then cases, each `kind` `required`, `forbidden`, or `exceptional`. Here `required` means a positive scenario that must work; it does not set the rule-level acceptance gate. A confirmed rule needs at least one required and one forbidden scenario. |
| `check` | `method` (test, assertion, review, proof, measurement, none), optional `ref`, and `strength` (exhaustive, bounded, sampled, human). |
| `evidence` | `result` (passed, failed, unknown, unmeasurable, out_of_scope), a `ref` to the result, `date`, `limitations`, and `provenance` (code version, rule revision, environment, workload, tool, period). |
| `depends_on` | Other rule ids this rule relies on. If one of them fails, this rule's pass counts as unknown. |

Rules files are JSON (`<app>.rules.json`), checked against [`rule-file.schema.json`](../tools/business-rules/rule-file.schema.json). JSON has no comments, so use `rationale` and `description` fields for explanations. `.yaml` and `.yml` files are still read if you prefer them (this needs PyYAML). See [`rules.example.json`](../tools/business-rules/templates/rules.example.json).

## Workflow

1. **Start from where the app is.** Idea only: answer discovery questions about one workflow. Partly specified: audit the spec for gaps and contradictions. Partly built: extract the rules the code implements and mark each intended or accidental.
2. **Confirm.** Each `proposed` rule is yours to confirm, change, or reject. Confirmation is what turns an assumption into a requirement.
3. **Add scenarios.** At least one case that must work and one that must be refused.
4. **Define a check** for every confirmed rule, then record the evidence it produces.
5. **Run the checker** and work through the gaps it lists.

```
python3 tools/business-rules/check_rules.py my-app.rules.json
```

Needs jsonschema (`pip install jsonschema`), plus PyYAML only for YAML files. Without jsonschema the checker stops with an error unless you pass `--skip-shape`.

Exit codes: 0 acceptable within the evidenced scope, 1 structural errors, 2 a confirmed rule failed, 3 blocked (a confirmed required rule is unknown, unmeasurable, out of scope, or uses a parameter that is not confirmed or has no value). `--allow-unknown` reports blockers but exits 0, for work in progress.

By default the checker also compares the file with `HEAD` (when it is tracked in git) and errors when a confirmed rule's statement, scenarios, check, `uses`, or `required` was changed, or the rule was removed, without a newer `decided_on` or a higher `revision`. This stops an implementation from weakening its own acceptance criteria. Run it before committing, since after the commit `HEAD` already contains the change. `--base <git-ref>` compares with another point in history; `--no-base` turns the comparison off; `--today YYYY-MM-DD` sets the date for expiry checks.

## One source of truth: parameters, assumptions, datasets

The file is the only place a rule's numbers, conditions and reference data are stated. Code, tests and configuration read them from it; they do not restate them. Three optional sections sit beside `rules`:

| Section | Holds | Key fields |
| --- | --- | --- |
| `assumptions` | Conditions rules and measurements hold under: workload, environment, scope, external facts. | `kind`, `status`, `source`, `valid_until` |
| `parameters` | Named numbers and settings: limits, thresholds, budgets, measured values. | `value`, `unit`, `origin`, `mutability`, `changeable_by`, `bounds`, `measurement`, `assumptions`, `review_by` |
| `datasets` | Static reference data (rates, catalogues), tracked by version. | `version`, `path`, `mutability`, `owner`, `review_by` |

A rule links to them with `uses: {parameters: [...], assumptions: [...], datasets: [...]}`, and its statement names a parameter (`above P-max-discount`) instead of containing the number.

**Origin** says where a value came from: `decided` (a person chose it), `measured` (taken from a measurement; record `measurement.date`, `workload`, `environment`, `tool`, `period`, `sample_size`), or `estimated` (a prediction or guess, so usually `proposed`).

**Mutability** says when it may change: `build` (fixed when the app is built or tested) or `runtime` (may change while the app runs). A runtime number should have `bounds`, so a bad change can be rejected without a redeploy.

**Who may change it** is `changeable_by`: `business_owner`, `developer`, `measurement`. A decided value changes only with a newer `decided_on` or a higher `revision`, the same as a rule. A measured value whose `changeable_by` includes `measurement` may be replaced by a newer measurement (a later `measurement.date`) without a new decision. Bounds, origin, mutability and `changeable_by` themselves always need a decision, so a change cannot grant itself permission.

What the checker adds:

- Errors: a rule or parameter pointing at an unknown id; an id reused across sections; a confirmed parameter with no value, decider, date or non-inferred source; a confirmed measured value with no `measurement.date`; a value outside its bounds; a confirmed parameter or assumption weakened or removed since the base commit.
- Warnings: expired assumptions (`valid_until`), overdue `review_by`, a runtime number without bounds, a rule whose evidence is older than a parameter it uses, a rule using an unconfirmed assumption.
- Blocking: a confirmed required rule that uses a parameter that is not confirmed or has no value is blocked (exit 3), because the rule cannot be satisfied with a guess.

Code reads the values with the exporter, which validates the file first and refuses unconfirmed parameters:

```
python3 tools/business-rules/export_params.py my-app.rules.json --mutability build --format env
python3 tools/business-rules/export_params.py my-app.rules.json --mutability runtime   # json, with bounds
```

Use `build` output for generated constants or deploy variables, and `runtime` output for a loader that reloads while the app runs. The runtime loader should reject values outside `bounds`. The checker cannot see a number hard-coded in source; a code review or a test that loads the exported value (and fails if the file and the code disagree) covers that gap.

Why these fields: they follow the books and papers in [research](research/research-review.md) and [books](research/books.md). Requirements, specifications and environmental assumptions are kept apart (Calinescu et al.); parameters say whether a value was stated or measured and who owns it (Spinner et al.); workload and deployment are separate from resource demand, so one can change without redoing the other (Palladio); a measurement carries the conditions it was taken under (Gregg; Smith and Williams); and expiry and revision keep an old claim from standing in for a current one. These support the design; none of them shows this format works. That is what using it will show.

## Dependencies

If a rule that passed depends on a rule that failed, its pass is downgraded to unknown in the report and exit code, so a required rule becomes blocked. If a dependency is merely unknown, unmeasurable, out of scope, or not confirmed, the checker warns. Proxies that are unconfirmed or failed do not resolve an unmeasurable rule. Dependency cycles are errors.

## Unknown versus unmeasurable

`unknown` means not checked yet. `unmeasurable` means no available check can decide the rule, and needs a `reason`. Neither counts as satisfied. For a required but unmeasurable rule, either add checkable proxy rules (`proxies`), add a human review check (`method: review`, `strength: human`) with the reviewer's result as evidence, or have the decision maker revise the rule or set `required: false` with a recorded reason. A `passed` result carries its `strength`: a sampled pass is a pass within that sample only.

## Rules the checker enforces

- Ids are unique and `depends_on` points at real rules.
- Confirmed rules have a decider, a date, a non-inferred source, and required and forbidden scenarios.
- `passed` or `failed` evidence needs a real check method and a result reference.
- An open question cannot be passed. Unmeasurable evidence needs a reason, and its proxies must be rules in the file.
- Confirmed rules must say whether they are required.
- No dependency cycles.

Warnings: missing scenarios on proposed or open rules, passed evidence with no stated check strength or provenance, and stale evidence dated before the rule's last decision or checked against an older `revision`.

## Tests

```
python3 -m unittest discover tools/business-rules/tests
```

## What it cannot do

It checks structure and recorded evidence. It cannot tell you a rule is right or that no rule is missing; that stays with you. Use the Claude skill, or any assistant, to help draw rules out, but only you confirm them.
