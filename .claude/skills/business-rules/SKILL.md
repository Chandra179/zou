---
name: business-rules
description: Draw out, record, and check an app's business rules in a rules file that separates confirmed decisions from inferred assumptions and open questions, and keeps the rules' numbers (limits, thresholds, budgets, measurements), assumptions, and reference data in that one file instead of in code. Use when the user wants to specify, audit, or extract business rules for any app (idea, partly specified, or partly built), asks where a number or config value should live, or asks what is confirmed, checked, or unknown.
---

# Business rules

Goal: a rules file (`<app>.rules.json`, shape in `rule-file.schema.json`, example in `templates/rules.example.json`, both in the tools folder below) where every rule says who decided it, which scenarios define it, how it is checked, and what the evidence is. Unknown is never treated as satisfied.

## Where the tools are

The checker, schema, example and tests live in the zou repo at `tools/business-rules/`, not in this folder. `<tools>` means that folder. When this skill is installed as a symlink, find it with `readlink -f <this skill folder>`, then `../../../tools/business-rules` from there. In the zou repo itself it is `tools/business-rules`.

## Ground rules

1. **Never mark a rule `confirmed` yourself.** Only the user (or a named decision maker they cite) confirms. What you infer is `proposed` with `source.kind: inferred`. Unresolved questions are `open`.
2. **Never weaken a confirmed rule, scenario, or check to make evidence pass.** A change to a confirmed rule needs the user's decision and a new `decided_on`.
3. **Every rule needs a required and a forbidden scenario.** Forbidden cases expose rules that are too permissive.
4. **Evidence comes from the check, not from your judgment.** Record `passed` or `failed` only with a real `check.method` and a `ref` to the result, plus provenance (code version, environment, workload, tool). State `check.strength` honestly: `exhaustive`, `bounded`, `sampled`, or `human`. A sampled pass is a pass within that sample only.
5. **Separate `unknown` from `unmeasurable`.** `unknown` means not checked yet. `unmeasurable` means no available check can decide the rule; record a `reason`. Never call such a rule satisfied. Resolve it by adding checkable proxy rules (`proxies`), a human review check (`method: review`, `strength: human`), or by asking the decision maker to revise the rule or mark it `required: false`.
6. **Mark each confirmed rule `required` true or false.** Required means an outcome, invariant, or hard constraint that blocks acceptance while unevidenced. Ask the user; do not guess.
7. **Do not report a correctness percentage.** Report counts by status and evidence, and list the gaps.
8. **Numbers live in `parameters`, not in statements or code.** When a rule contains a limit, threshold, budget, rate or other number, record it as a parameter (`value`, `unit`, `origin`, `mutability`) and have the rule name it through `uses`. Never invent a value: if the user has not decided it, record it `proposed` or leave `value: null`, and ask. A measured value needs its `measurement` context (date, workload assumption, environment, tool, period). Conditions the numbers hold under belong in `assumptions`, with a `valid_until` when they can lapse; static reference data belongs in `datasets`.
9. **Ask who may change each parameter and when.** `mutability` is `build` or `runtime`; `changeable_by` lists `business_owner`, `developer`, `measurement`. Give a runtime number `bounds`. Never widen bounds or grant a change permission to get past a check.

## Pick the entry point from the app's state

- **Idea only (discovery):** ask about one bounded workflow at a time. Walk the prompts: what happens before, during, and after; missing, invalid, outdated, or contradictory data; overlapping, late, or repeated actions; dependency failure or interruption; who may act or see the data; how an unfinished or wrong outcome is found and recovered. Offer business alternatives in everyday language. Write each answer as a `proposed` rule and ask the user to confirm, change, or reject it. For every number a rule needs, also ask who decides it, whether it can change while the app runs, and what it assumes (load, environment, scope); record those as parameters and assumptions.
- **Partly specified (audit):** read the spec and look for contradictions, ambiguities, missing rules, and assumptions presented as decisions. Turn each into a rule record or an `open` question, and ask the user. Move numbers written inside statements into parameters.
- **Partly built (extraction):** read the code and list the rules it actually implements, each as `proposed` with `source.kind: code` and a file reference. Ask the user whether each is intended or accidental. List the numbers hard-coded in the source as `proposed` parameters with `source.kind: code`; ask whether each should be fixed at build time or changeable at runtime, and by whom. Then look for rules the code never implements (unchecked inputs, missing authorization, no failure handling) and add them as `open`.

Ask in small batches, not a long questionnaire. Record the answer and its date before moving on.

## Loop

1. Update the rules file.
2. Run `python3 <tools>/check_rules.py <file>` every time, before committing. It compares against the last commit and errors if a confirmed rule was weakened. Fix structural errors. Do not silence them by loosening the file, and never pass `--no-base` or `--skip-shape` to get past an error.
3. Show the user the report: rules awaiting their decision, open questions, parameters that are not confirmed, expired assumptions, confirmed rules with no check, and confirmed rules that are blocked (unknown, unmeasurable, out of scope, or using an unsettled parameter) or failed. To give code the values, run `python3 <tools>/export_params.py <file> --mutability build|runtime --format json|flat|env`; it refuses unconfirmed parameters.
4. Pick the next gap, with the user, and repeat.

Bump a rule's `revision` (and `decided_on`) only when the user re-decides it, never to get past the weakening check. If a rule's dependency (`depends_on`) failed, the checker downgrades the dependent rule's pass to unknown: report that, do not hide it.

Exit codes: 0 acceptable within the evidenced scope, 1 structural errors, 2 a confirmed rule failed, 3 blocked (a confirmed required rule is unknown, unmeasurable, out of scope, or uses an unsettled parameter). Use `--allow-unknown` while work is in progress. By default the checker compares with `HEAD` (when the file is in git) and errors when a confirmed rule's statement, scenarios, check, or `required` changed without a newer `decided_on` or higher `revision`; `--base <git-ref>` picks another base and `--no-base` turns it off. The script needs jsonschema (`--skip-shape` skips the shape checks); PyYAML only if the rules file is YAML. Write rules files as JSON.

## Limits to tell the user

The checker verifies structure and recorded evidence. It cannot tell whether a rule is right or complete, and it cannot see a number hard-coded in source: say so, and suggest a test that loads the exported value. Rules nobody stated stay invisible, so keep asking what is still missing.
