#!/usr/bin/env python3
"""Check a Zou business-rule file and print an evidence report.

Usage: check_rules.py RULES.yaml [--strict] [--json]

Exit codes: 0 ok, 1 structural errors, 2 a rule is violated,
            3 --strict and a confirmed rule is not verified.

This checks structure and recorded evidence status only. It cannot tell
whether a rule is the right rule: that is what `confirmed` records.
Needs PyYAML; uses jsonschema for shape checks when installed.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")



class _Loader(yaml.SafeLoader):
    """Keep ISO dates as strings so they match the schema."""


_Loader.yaml_implicit_resolvers = {
    k: [(t, r) for t, r in v if t != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

SCHEMA = Path(__file__).resolve().parent.parent / "rule-file.schema.json"


def shape_errors(doc):
    try:
        import jsonschema
    except ImportError:
        return [], "jsonschema not installed: shape checks skipped (pip install jsonschema)"
    validator = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text()))
    errs = []
    for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in e.absolute_path) or "(root)"
        errs.append(f"shape: {where}: {e.message}")
    return errs, None


def check(doc):
    errors, warnings = [], []
    rules = doc.get("rules") or []
    ids = [r.get("id") for r in rules if isinstance(r, dict)]
    for rid, n in Counter(ids).items():
        if n > 1:
            errors.append(f"{rid}: duplicate id")
    known = set(ids)

    for r in rules:
        if not isinstance(r, dict):
            continue
        rid = r.get("id", "?")
        status = r.get("status")
        kinds = {s.get("kind") for s in r.get("scenarios") or [] if isinstance(s, dict)}
        method = (r.get("check") or {}).get("method")
        ev = (r.get("evidence") or {}).get("result")

        for d in r.get("depends_on") or []:
            if d not in known:
                errors.append(f"{rid}: depends_on unknown rule {d}")
            if d == rid:
                errors.append(f"{rid}: depends on itself")

        if status == "confirmed":
            for field in ("decided_by", "decided_on"):
                if not r.get(field):
                    errors.append(f"{rid}: confirmed but missing {field}")
            if (r.get("source") or {}).get("kind") in (None, "inferred"):
                errors.append(f"{rid}: confirmed but source is missing or 'inferred'")
            for k in ("required", "forbidden"):
                if k not in kinds:
                    errors.append(f"{rid}: confirmed but has no {k} scenario")
        else:
            for k in ("required", "forbidden"):
                if k not in kinds:
                    warnings.append(f"{rid}: no {k} scenario yet")
            if status == "proposed" and (r.get("source") or {}).get("kind") != "inferred" and r.get("source"):
                warnings.append(f"{rid}: proposed but source is not 'inferred'; confirm it?")

        if ev in ("verified", "violated"):
            if method in (None, "none"):
                errors.append(f"{rid}: evidence '{ev}' recorded but check method is none/missing")
            if not (r.get("evidence") or {}).get("ref"):
                errors.append(f"{rid}: evidence '{ev}' has no ref to the result")
            if status != "confirmed":
                warnings.append(f"{rid}: evidence '{ev}' on a rule that is not confirmed")
        if ev == "verified" and not (r.get("check") or {}).get("strength"):
            warnings.append(f"{rid}: verified but check.strength not stated")
        if status == "open" and ev == "verified":
            errors.append(f"{rid}: open question cannot be verified")
    return errors, warnings


def report(doc):
    rules = [r for r in doc.get("rules") or [] if isinstance(r, dict)]
    confirmed = [r for r in rules if r.get("status") == "confirmed"]

    def ev(r):
        return (r.get("evidence") or {}).get("result", "unknown")

    def method(r):
        return (r.get("check") or {}).get("method", "none")

    rep = {
        "app": doc.get("app"),
        "rules_by_status": dict(Counter(r.get("status") for r in rules)),
        "confirmed_evidence": dict(Counter(ev(r) for r in confirmed)),
        "violated": [r["id"] for r in confirmed if ev(r) == "violated"],
        "confirmed_without_check": [r["id"] for r in confirmed if method(r) == "none"],
        "confirmed_unknown": [r["id"] for r in confirmed if ev(r) == "unknown"],
        "awaiting_confirmation": [r["id"] for r in rules if r.get("status") == "proposed"],
        "open_questions": [r["id"] for r in rules if r.get("status") == "open"],
    }
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    try:
        doc = yaml.load(Path(a.file).read_text(), Loader=_Loader)
    except (OSError, yaml.YAMLError) as e:
        print(f"cannot read {a.file}: {e}", file=sys.stderr)
        return 1
    if not isinstance(doc, dict):
        print("file must be a YAML mapping with 'app' and 'rules'", file=sys.stderr)
        return 1

    errors, note = shape_errors(doc)
    if not errors:
        e2, warnings = check(doc)
        errors += e2
    else:
        warnings = []
    if note:
        warnings.append(note)
    rep = report(doc) if not errors else None

    if a.json:
        print(json.dumps({"errors": errors, "warnings": warnings, "report": rep}, indent=2))
    else:
        for e in errors:
            print(f"ERROR   {e}")
        for w in warnings:
            print(f"WARNING {w}")
        if rep:
            print(f"\nApp: {rep['app']}")
            print(f"Rules by status:        {rep['rules_by_status']}")
            print(f"Confirmed rule evidence: {rep['confirmed_evidence']}")
            for label, key in (("Violated", "violated"),
                               ("Confirmed, no check defined", "confirmed_without_check"),
                               ("Confirmed, evidence unknown", "confirmed_unknown"),
                               ("Proposed, awaiting your decision", "awaiting_confirmation"),
                               ("Open questions", "open_questions")):
                print(f"{label}: {', '.join(rep[key]) or '-'}")
            print("\nNo correctness percentage is reported on purpose: unknown is not satisfied.")

    if errors:
        return 1
    if rep["violated"]:
        return 2
    if a.strict and (rep["confirmed_unknown"] or rep["confirmed_evidence"].get("out_of_scope")):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
