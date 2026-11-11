# Zou

An evidence-based approach to evaluating software changes: state claims, check
them under explicit conditions, record evidence and uncertainty, then decide
what to accept or revise.

The repository contains the conceptual evaluation model and a focused first
tool for specifying and checking behavioral business rules. The business-rules
tool is not yet a general evaluator for design, implementation, resource, or
runtime claims.

## Documents

- [Evaluation model](evaluation-model.yaml): the general method
- [Business rules: file format and how-to](docs/business-rules-howto.md)
- [Measurement-driven development](docs/measurement-driven-development.md): design notes; resource prediction is deferred
- [Research review](docs/research/research-review.md)
- [Related books and reading order](docs/research/books.md)

## Tools

- [`tools/business-rules/`](tools/business-rules/check_rules.py): the checker, parameter exporter, schema, example and tests. Plain Python, no Claude needed.
- [`business-rules` Claude skill](.claude/skills/business-rules/SKILL.md): optional, Claude-installed helper for drawing out business rules. It supports the focused tool above, not the full evaluation model. Install it for your current user with `tools/install-skill.sh`.
