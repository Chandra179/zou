#!/usr/bin/env python3
"""Export parameters from a Zou rules file so code reads them instead of restating them.

Usage: export_params.py RULES.yaml [--mutability build|runtime] [--format json|flat|env]
                                   [--include-unsettled] [--skip-shape]

Formats:
  json  (default) {"app", "parameters": {id: {value, unit, mutability, origin}}, "datasets": {...}}
  flat  {id: value}, for a loader or a generated constants module
  env   ID=value lines (id upper-cased, other characters become '_'), for build or deploy scripts

The file is validated first. Nothing is exported if it has errors. Parameters that are
not confirmed, or have no value, are refused unless --include-unsettled is given, so an
unconfirmed guess cannot reach the code by accident.

Use --mutability build for values compiled or generated into the app, and --mutability
runtime for values loaded while it runs. A runtime loader should still reject values
outside the parameter's `bounds`: they are included in the json format.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rules as cr  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--mutability", choices=("build", "runtime"), help="only export parameters of this kind")
    ap.add_argument("--format", choices=("json", "flat", "env"), default="json")
    ap.add_argument("--include-unsettled", action="store_true",
                    help="also export parameters that are not confirmed or have no value")
    ap.add_argument("--skip-shape", action="store_true", help="skip JSON Schema shape checks (not recommended)")
    a = ap.parse_args()

    path = Path(a.file)
    try:
        doc = cr.yaml.load(path.read_text(), Loader=cr._Loader)
    except (OSError, cr.yaml.YAMLError) as e:
        print(f"cannot read {a.file}: {e}", file=sys.stderr)
        return 1
    if not isinstance(doc, dict):
        print("file must be a YAML mapping", file=sys.stderr)
        return 1

    errors = []
    if not a.skip_shape:
        try:
            errors = cr.shape_errors(doc)
        except ImportError:
            print("jsonschema is required: pip install jsonschema (or pass --skip-shape)", file=sys.stderr)
            return 1
    if not errors:
        errors = cr.check(doc, base_dir=path.resolve().parent)[0]
    if errors:
        for e in errors:
            print(f"ERROR   {e}", file=sys.stderr)
        print("Nothing exported: fix the errors first.", file=sys.stderr)
        return 1

    params, refused = {}, []
    for p in cr.items(doc, "parameters"):
        if a.mutability and p.get("mutability") != a.mutability:
            continue
        if cr.unsettled(p) and not a.include_unsettled:
            refused.append(p["id"])
            continue
        params[p["id"]] = p
    for pid in refused:
        print(f"skipped {pid}: not confirmed or has no value (use --include-unsettled to export it)", file=sys.stderr)

    if a.format == "flat":
        out = {pid: p.get("value") for pid, p in params.items()}
    elif a.format == "env":
        lines = []
        for pid, p in params.items():
            v = p.get("value")
            if v is None:
                continue
            v = str(v).lower() if isinstance(v, bool) else str(v)
            name = re.sub(r"[^A-Za-z0-9]", "_", pid).upper()
            quoted = json.dumps(v) if re.search(r"\s", v) else v
            lines.append(f"{name}={quoted}")
        print("\n".join(lines))
        return 0
    else:
        out = {
            "app": doc.get("app"),
            "parameters": {
                pid: {k: p.get(k) for k in ("value", "unit", "mutability", "origin", "bounds") if p.get(k) is not None}
                for pid, p in params.items()
            },
            "datasets": {
                d["id"]: {k: d.get(k) for k in ("version", "path", "mutability") if d.get(k) is not None}
                for d in cr.items(doc, "datasets") if not a.mutability or d.get("mutability") == a.mutability
            },
        }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
