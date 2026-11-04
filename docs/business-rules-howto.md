# Business rules: file format and how-to

Applies the [evaluation pattern](../evaluation-pattern.yaml) to one problem: getting an app's business rules specified correctly. The format and [checker](../tools/business-rules/check_rules.py) are plain Python and need no Claude. The optional [Claude skill](../.claude/skills/business-rules/SKILL.md) helps draw rules out.

## The idea

Write every rule as a record that answers: who decided it, which concrete cases define it, how it is checked, and what the evidence says. Then a script reports what is confirmed, what is only assumed, and what is unknown. There is no overall score, because unknown is not satisfied.

## Rule record

| Field | Meaning |
| --- | --- |
| `id`, `statement` | Stable name and the rule in plain language (EARS wording is optional). |
| `status` | `confirmed`: a decision maker decided it. `proposed`: inferred, awaiting a decision. `open`: an unresolved question. |
| `revision` | Integer, starting at 1. Bump it each time a decision maker re-decides a confirmed rule, including several times on one day. |
| `required` | `true` for an outcome, invariant, or hard constraint that blocks acceptance while unevidenced. Mandatory on confirmed rules. |
| `source`, `decided_by`, `decided_on` | Where it came from and who decided it. Required for `confirmed`; the source cannot be `inferred`. |
| `scenarios` | Concrete given / when / then cases, each `required`, `forbidden`, or `exceptional`. A confirmed rule needs at least one required and one forbidden scenario. |
| `check` | `method` (test, assertion, review, proof, measurement, none), optional `ref`, and `strength` (exhaustive, bounded, sampled, human). |
| `evidence` | `result` (passed, failed, unknown, unmeasurable, out_of_scope), a `ref` to the result, `date`, `limitations`, and `provenance` (code version, rule revision, environment, workload, tool, period). |
| `depends_on` | Other rule ids this rule relies on. If one of them fails, this rule's pass counts as unknown. |

See [`rules.example.yaml`](../tools/business-rules/templates/rules.example.yaml).

## Workflow

1. **Start from where the app is.** Idea only: answer discovery questions about one workflow. Partly specified: audit the spec for gaps and contradictions. Partly built: extract the rules the code implements and mark each intended or accidental.
2. **Confirm.** Each `proposed` rule is yours to confirm, change, or reject. Confirmation is what turns an assumption into a requirement.
3. **Add scenarios.** At least one case that must work and one that must be refused.
4. **Define a check** for every confirmed rule, then record the evidence it produces.
5. **Run the checker** and work through the gaps it lists.

```
python3 tools/business-rules/check_rules.py my-app.rules.yaml
```

Needs PyYAML and jsonschema (`pip install pyyaml jsonschema`). Without jsonschema the checker stops with an error unless you pass `--skip-shape`.

Exit codes: 0 acceptable within the evidenced scope, 1 structural errors, 2 a confirmed rule failed, 3 blocked (a confirmed required rule is unknown, unmeasurable, or out of scope). `--allow-unknown` reports blockers but exits 0, for work in progress.

By default the checker also compares the file with `HEAD` (when it is tracked in git) and errors when a confirmed rule's statement, scenarios, check, or `required` was changed, or the rule was removed, without a newer `decided_on` or a higher `revision`. This stops an implementation from weakening its own acceptance criteria. Run it before committing, since after the commit `HEAD` already contains the change. `--base <git-ref>` compares with another point in history; `--no-base` turns the comparison off.

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
