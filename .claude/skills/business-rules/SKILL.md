---
name: business-rules
description: Draw out, record, and check an app's business rules in a rules file that separates confirmed decisions from inferred assumptions and open questions. Use when the user wants to specify, audit, or extract business rules for any app (idea, partly specified, or partly built), or asks what is confirmed, checked, or unknown.
---

# Business rules

Goal: a rules file (`<app>.rules.yaml`, shape in `rule-file.schema.json`, example in `templates/rules.example.yaml`) where every rule says who decided it, which scenarios define it, how it is checked, and what the evidence is. Unknown is never treated as satisfied.

## Ground rules

1. **Never mark a rule `confirmed` yourself.** Only the user (or a named decision maker they cite) confirms. What you infer is `proposed` with `source.kind: inferred`. Unresolved questions are `open`.
2. **Never weaken a confirmed rule, scenario, or check to make evidence pass.** A change to a confirmed rule needs the user's decision and a new `decided_on`.
3. **Every rule needs a required and a forbidden scenario.** Forbidden cases expose rules that are too permissive.
4. **Evidence comes from the check, not from your judgment.** Record `verified` only with a real `check.method` and a `ref` to the result. State `check.strength` honestly: `exhaustive`, `bounded`, `sampled`, or `human`.
5. **Do not report a correctness percentage.** Report counts by status and evidence, and list the gaps.

## Pick the entry point from the app's state

- **Idea only (discovery):** ask about one bounded workflow at a time. Walk the prompts: what happens before, during, and after; missing, invalid, outdated, or contradictory data; overlapping, late, or repeated actions; dependency failure or interruption; who may act or see the data; how an unfinished or wrong outcome is found and recovered. Offer business alternatives in everyday language. Write each answer as a `proposed` rule and ask the user to confirm, change, or reject it.
- **Partly specified (audit):** read the spec and look for contradictions, ambiguities, missing rules, and assumptions presented as decisions. Turn each into a rule record or an `open` question, and ask the user.
- **Partly built (extraction):** read the code and list the rules it actually implements, each as `proposed` with `source.kind: code` and a file reference. Ask the user whether each is intended or accidental. Then look for rules the code never implements (unchecked inputs, missing authorization, no failure handling) and add them as `open`.

Ask in small batches, not a long questionnaire. Record the answer and its date before moving on.

## Loop

1. Update the rules file.
2. Run `python3 scripts/check_rules.py <file>` (path relative to this skill). Fix structural errors. Do not silence them by loosening the file.
3. Show the user the report: rules awaiting their decision, open questions, confirmed rules with no check, and confirmed rules with unknown or violated evidence.
4. Pick the next gap, with the user, and repeat.

Exit codes: 1 structural errors, 2 a confirmed rule is violated, 3 (`--strict`) a confirmed rule is not verified. The script needs PyYAML, and uses jsonschema for shape checks when installed.

## Limits to tell the user

The checker verifies structure and recorded evidence. It cannot tell whether a rule is right or complete. Rules nobody stated stay invisible, so keep asking what is still missing.
