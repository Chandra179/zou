# zou

## Documents

- [Conceptual evaluation pattern](evaluation-pattern.yaml): the method
- [Business rules: file format and how-to](docs/business-rules-howto.md)
- [Measurement-driven development](docs/measurement-driven-development.md): design notes; resource prediction is deferred
- [Research review](docs/research/research-review.md)
- [Related books and reading order](docs/research/books.md)

## Tools

- [`tools/business-rules/`](tools/business-rules/check_rules.py): the checker, schema, example and tests. Plain Python, no Claude needed.
- [`business-rules` Claude skill](.claude/skills/business-rules/SKILL.md): optional helper for drawing rules out. Install it for every project with `tools/install-skill.sh`.
