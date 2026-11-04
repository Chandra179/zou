# Business rules: file format and how-to

Applies the [evaluation pattern](../evaluation-pattern.yaml) to one problem: getting an app's business rules specified correctly. The format and checker live in the [`business-rules` skill](../.claude/skills/business-rules/SKILL.md).

## The idea

Write every rule as a record that answers: who decided it, which concrete cases define it, how it is checked, and what the evidence says. Then a script reports what is confirmed, what is only assumed, and what is unknown. There is no overall score, because unknown is not satisfied.

## Rule record

| Field | Meaning |
| --- | --- |
| `id`, `statement` | Stable name and the rule in plain language (EARS wording is optional). |
| `status` | `confirmed`: a decision maker decided it. `proposed`: inferred, awaiting a decision. `open`: an unresolved question. |
| `source`, `decided_by`, `decided_on` | Where it came from and who decided it. Required for `confirmed`; the source cannot be `inferred`. |
| `scenarios` | Concrete given / when / then cases, each `required`, `forbidden`, or `exceptional`. A confirmed rule needs at least one required and one forbidden scenario. |
| `check` | `method` (test, assertion, review, proof, measurement, none), optional `ref`, and `strength` (exhaustive, bounded, sampled, human). |
| `evidence` | `result` (verified, violated, unknown, out_of_scope), a `ref` to the result, `date`, and `limitations`. |
| `depends_on` | Other rule ids this rule relies on. |

See [`rules.example.yaml`](../.claude/skills/business-rules/templates/rules.example.yaml).

## Workflow

1. **Start from where the app is.** Idea only: answer discovery questions about one workflow. Partly specified: audit the spec for gaps and contradictions. Partly built: extract the rules the code implements and mark each intended or accidental.
2. **Confirm.** Each `proposed` rule is yours to confirm, change, or reject. Confirmation is what turns an assumption into a requirement.
3. **Add scenarios.** At least one case that must work and one that must be refused.
4. **Define a check** for every confirmed rule, then record the evidence it produces.
5. **Run the checker** and work through the gaps it lists.

```
python3 .claude/skills/business-rules/scripts/check_rules.py my-app.rules.yaml
```

Needs PyYAML (`pip install pyyaml`). With jsonschema installed it also validates the shape. Exit codes: 1 structural errors, 2 a confirmed rule is violated, 3 (`--strict`) a confirmed rule is not verified.

## Rules the checker enforces

- Ids are unique and `depends_on` points at real rules.
- Confirmed rules have a decider, a date, a non-inferred source, and required and forbidden scenarios.
- `verified` or `violated` evidence needs a real check method and a result reference.
- An open question cannot be verified.

Missing scenarios on proposed or open rules are warnings, as is verified evidence with no stated check strength.

## What it cannot do

It checks structure and recorded evidence. It cannot tell you a rule is right or that no rule is missing; that stays with you. Use the Claude skill, or any assistant, to help draw rules out, but only you confirm them.
