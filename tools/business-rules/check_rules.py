#!/usr/bin/env python3
"""Check a Zou business-rule file and print an evidence report.

Usage: check_rules.py RULES.yaml [--allow-unknown] [--base GIT_REF | --no-base] [--skip-shape] [--json]

Exit codes:
  0  acceptable within the evidenced scope
  1  structural errors, or a confirmed rule weakened since the base commit
  2  a confirmed rule failed
  3  blocked: a confirmed required rule is unknown, unmeasurable, or out of
     scope (--allow-unknown reports the blockers but exits 0)

This checks structure and recorded evidence only. It cannot tell whether a
rule is the right rule: that is what `confirmed` records. Needs PyYAML and
jsonschema (or --skip-shape). Compares against HEAD by default when the file is
in git; a weakened confirmed rule needs a newer decided_on or higher revision.
"""
import argparse
import json
import subprocess
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

SCHEMA = Path(__file__).resolve().parent / "rule-file.schema.json"
UNSETTLED = ("unknown", "unmeasurable", "out_of_scope")
GUARDED = ("statement", "scenarios", "check", "required")


def shape_errors(doc):
    import jsonschema
    validator = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text()))
    errs = []
    for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in e.absolute_path) or "(root)"
        errs.append(f"shape: {where}: {e.message}")
    return errs


def ev_of(r):
    return (r.get("evidence") or {}).get("result", "unknown")


def rev_of(r):
    v = r.get("revision")
    return v if isinstance(v, int) else 1


def effective_results(rules):
    """Recorded result per rule id, except a pass is downgraded to 'unknown' when a
    dependency (transitively) failed. Returns (results, {id: failed dependency})."""
    by_id = {r.get("id"): r for r in rules}
    memo, why = {}, {}

    def eff(rid, stack):
        if rid in memo:
            return memo[rid]
        r = by_id.get(rid)
        if r is None or rid in stack:
            return "unknown"
        res = ev_of(r)
        if res == "passed":
            for d in r.get("depends_on") or []:
                if d in by_id and eff(d, stack | {rid}) == "failed":
                    res, why[rid] = "unknown", d
                    break
        memo[rid] = res
        return res

    return {rid: eff(rid, frozenset()) for rid in by_id}, why


def find_cycle(rules):
    by_id = {r.get("id"): r for r in rules}
    state = {}

    def visit(rid, path):
        if state.get(rid) == "done" or rid not in by_id:
            return None
        if state.get(rid) == "active":
            return path[path.index(rid):] + [rid]
        state[rid] = "active"
        for d in by_id[rid].get("depends_on") or []:
            if d != rid:
                found = visit(d, path + [rid])
                if found:
                    return found
        state[rid] = "done"
        return None

    for rid in by_id:
        found = visit(rid, [])
        if found:
            return found
    return None


def check(doc):
    errors, warnings = [], []
    rules = [r for r in doc.get("rules") or [] if isinstance(r, dict)]
    ids = [r.get("id") for r in rules]
    for rid, n in Counter(ids).items():
        if n > 1:
            errors.append(f"{rid}: duplicate id")
    known = set(ids)
    by_id = {r.get("id"): r for r in rules}
    results, downgraded = effective_results(rules)
    cycle = find_cycle(rules)
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle))

    for r in rules:
        rid = r.get("id", "?")
        status = r.get("status")
        evidence = r.get("evidence") or {}
        ev = ev_of(r)
        check_ = r.get("check") or {}
        method, strength = check_.get("method"), check_.get("strength")
        kinds = {s.get("kind") for s in r.get("scenarios") or [] if isinstance(s, dict)}

        for d in r.get("depends_on") or []:
            if d not in known:
                errors.append(f"{rid}: depends_on unknown rule {d}")
            if d == rid:
                errors.append(f"{rid}: depends on itself")
            dep = by_id.get(d)
            if dep is not None and d != rid and ev == "passed":
                dres = results.get(d)
                if rid in downgraded and downgraded[rid] == d:
                    warnings.append(f"{rid}: pass downgraded to unknown: dependency {d} failed")
                elif dep.get("status") != "confirmed" or dres in UNSETTLED:
                    warnings.append(f"{rid}: passed, but dependency {d} is not confirmed and passed "
                                    f"(status {dep.get('status')}, evidence {dres})")

        if status == "confirmed":
            for field in ("decided_by", "decided_on"):
                if not r.get(field):
                    errors.append(f"{rid}: confirmed but missing {field}")
            if (r.get("source") or {}).get("kind") in (None, "inferred"):
                errors.append(f"{rid}: confirmed but source is missing or 'inferred'")
            if not isinstance(r.get("required"), bool):
                errors.append(f"{rid}: confirmed but 'required' (true/false) is not set")
            for k in ("required", "forbidden"):
                if k not in kinds:
                    errors.append(f"{rid}: confirmed but has no {k} scenario")
        else:
            for k in ("required", "forbidden"):
                if k not in kinds:
                    warnings.append(f"{rid}: no {k} scenario yet")

        if ev in ("passed", "failed"):
            if method in (None, "none"):
                errors.append(f"{rid}: evidence '{ev}' recorded but check method is none/missing")
            if not evidence.get("ref"):
                errors.append(f"{rid}: evidence '{ev}' has no ref to the result")
            if status != "confirmed":
                warnings.append(f"{rid}: evidence '{ev}' on a rule that is not confirmed")
            if not evidence.get("provenance"):
                warnings.append(f"{rid}: evidence '{ev}' has no provenance (version, environment, workload...)")
        if ev == "passed" and not strength:
            warnings.append(f"{rid}: passed but check.strength not stated")
        if ev == "unmeasurable":
            if not evidence.get("reason"):
                errors.append(f"{rid}: unmeasurable but no evidence.reason")
            usable = []
            for p in evidence.get("proxies") or []:
                if p not in known:
                    errors.append(f"{rid}: proxy {p} is not a rule in this file")
                elif by_id[p].get("status") != "confirmed":
                    warnings.append(f"{rid}: proxy {p} is not confirmed yet, so it does not resolve this rule")
                elif results.get(p) == "failed":
                    warnings.append(f"{rid}: proxy {p} failed, so it does not resolve this rule")
                else:
                    usable.append(p)
            if status == "confirmed" and r.get("required") and not usable \
                    and not (method == "review" and strength == "human"):
                warnings.append(f"{rid}: required and unmeasurable: add proxies, a human review check, "
                                "or have the decision maker revise or relax the rule")
        if status == "open" and ev == "passed":
            errors.append(f"{rid}: open question cannot be passed")

        d_on, e_on = r.get("decided_on"), evidence.get("date")
        if d_on and e_on and e_on < d_on:
            warnings.append(f"{rid}: stale evidence: dated {e_on}, before the rule was last decided ({d_on})")
        try:
            ev_rev = int((evidence.get("provenance") or {}).get("rule_revision"))
        except (TypeError, ValueError):
            ev_rev = None
        if ev_rev is not None and ev_rev < rev_of(r):
            warnings.append(f"{rid}: stale evidence: checked rule revision {ev_rev}, rule is now revision {rev_of(r)}")
    return errors, warnings


def weakened(doc, base):
    """Errors for confirmed rules in `base` that were changed or dropped without a newer decision."""
    errs = []
    now = {r.get("id"): r for r in doc.get("rules") or [] if isinstance(r, dict)}
    for old in base.get("rules") or []:
        if not isinstance(old, dict) or old.get("status") != "confirmed":
            continue
        rid = old.get("id")
        cur = now.get(rid)
        if cur is None:
            errs.append(f"{rid}: confirmed rule removed since base")
            continue
        newer = (cur.get("decided_on") or "") > (old.get("decided_on") or "") \
            or rev_of(cur) > rev_of(old)
        if cur.get("status") != "confirmed" and not newer:
            errs.append(f"{rid}: no longer confirmed since base, with no newer decided_on or higher revision")
            continue
        changed = [f for f in GUARDED if cur.get(f) != old.get(f)]
        if changed and not newer:
            errs.append(f"{rid}: changed {', '.join(changed)} since base without a newer decided_on "
                        "or higher revision")
    return errs


def load_base(path, ref):
    try:
        cwd = path.resolve().parent
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True,
                             text=True, check=True).stdout.strip()
        rel = path.resolve().relative_to(Path(top).resolve()).as_posix()
        out = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=top, capture_output=True,
                             text=True, check=True).stdout
        doc = yaml.load(out, Loader=_Loader)
        return doc if isinstance(doc, dict) else None, None
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        return None, f"--base {ref}: could not read the file at that ref ({e.__class__.__name__}); weakening check skipped"


def report(doc):
    rules = [r for r in doc.get("rules") or [] if isinstance(r, dict)]
    confirmed = [r for r in rules if r.get("status") == "confirmed"]
    req = [r for r in confirmed if r.get("required")]
    opt = [r for r in confirmed if not r.get("required")]
    results, downgraded = effective_results(rules)

    def ev_of(r):  # effective result: a pass resting on a failed dependency counts as unknown
        return results[r["id"]]

    def ids(rs):
        return [r["id"] for r in rs]

    return {
        "app": doc.get("app"),
        "rules_by_status": dict(Counter(r.get("status") for r in rules)),
        "confirmed_evidence": dict(Counter(ev_of(r) for r in confirmed)),
        "failed": ids(r for r in confirmed if ev_of(r) == "failed"),
        "downgraded": [f"{k} (dependency {v} failed)" for k, v in downgraded.items()],
        "blocked_unchecked": ids(r for r in req if ev_of(r) == "unknown"),
        "blocked_unmeasurable": ids(r for r in req if ev_of(r) == "unmeasurable"),
        "blocked_out_of_scope": ids(r for r in req if ev_of(r) == "out_of_scope"),
        "optional_gaps": ids(r for r in opt if ev_of(r) in UNSETTLED),
        "confirmed_without_check": ids(r for r in confirmed if (r.get("check") or {}).get("method", "none") == "none"),
        "sampled_passes": ids(r for r in confirmed if ev_of(r) == "passed"
                              and (r.get("check") or {}).get("strength") == "sampled"),
        "awaiting_confirmation": ids(r for r in rules if r.get("status") == "proposed"),
        "open_questions": ids(r for r in rules if r.get("status") == "open"),
    }


LABELS = (
    ("Failed", "failed"),
    ("Passed but downgraded to unknown", "downgraded"),
    ("Blocked, required, not checked yet", "blocked_unchecked"),
    ("Blocked, required, unmeasurable (needs proxies, human review, or a decision)", "blocked_unmeasurable"),
    ("Blocked, required, out of scope", "blocked_out_of_scope"),
    ("Optional rules with no settled evidence (not blocking)", "optional_gaps"),
    ("Confirmed, no check defined", "confirmed_without_check"),
    ("Passed on sampled evidence only", "sampled_passes"),
    ("Proposed, awaiting your decision", "awaiting_confirmation"),
    ("Open questions", "open_questions"),
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--allow-unknown", action="store_true", help="work in progress: report blockers but exit 0")
    ap.add_argument("--base", metavar="GIT_REF",
                    help="error if confirmed rules were weakened since this ref (default: HEAD, when the file is in git)")
    ap.add_argument("--no-base", action="store_true", help="skip the weakening check")
    ap.add_argument("--skip-shape", action="store_true", help="skip JSON Schema shape checks (not recommended)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    path = Path(a.file)
    try:
        doc = yaml.load(path.read_text(), Loader=_Loader)
    except (OSError, yaml.YAMLError) as e:
        print(f"cannot read {a.file}: {e}", file=sys.stderr)
        return 1
    if not isinstance(doc, dict):
        print("file must be a YAML mapping with 'app' and 'rules'", file=sys.stderr)
        return 1

    errors, warnings = [], []
    if a.skip_shape:
        warnings.append("shape checks skipped (--skip-shape)")
    else:
        try:
            import jsonschema  # noqa: F401
        except ImportError:
            print("jsonschema is required for shape checks: pip install jsonschema "
                  "(or pass --skip-shape to skip them)", file=sys.stderr)
            return 1
        errors = shape_errors(doc)
    if not errors:
        e2, w2 = check(doc)
        errors += e2
        warnings += w2
    if not errors and not a.no_base:
        base, bnote = load_base(path, a.base or "HEAD")
        if bnote and a.base:
            warnings.append(bnote)
        elif base:
            errors += weakened(doc, base)
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
            print(f"Rules by status:         {rep['rules_by_status']}")
            print(f"Confirmed rule evidence: {rep['confirmed_evidence']}")
            for label, key in LABELS:
                print(f"{label}: {', '.join(rep[key]) or '-'}")
            print("\nNo correctness percentage is reported on purpose: unknown is not satisfied.")

    if errors:
        return 1
    if rep["failed"]:
        return 2
    blocked = rep["blocked_unchecked"] or rep["blocked_unmeasurable"] or rep["blocked_out_of_scope"]
    if blocked and not a.allow_unknown:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
