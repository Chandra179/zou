"""Tests for assumptions, parameters, datasets, and export_params.py. Run:

    python3 -m unittest discover tools/business-rules/tests
"""
import json
import subprocess
import sys
import unittest

import test_check_rules as base
from test_check_rules import SKILL, ev, rule

EXPORT = SKILL / "export_params.py"

ASSUMPTION = """\
  - id: {id}
    statement: peak load
    status: confirmed
    source: {{kind: stakeholder, ref: ops}}
    decided_by: Sam
    decided_on: 2026-11-04
    valid_until: {valid_until}
"""

PARAM = """\
  - id: {id}
    value: {value}
    unit: ms
    status: {status}
    origin: {origin}
    mutability: {mutability}
    source: {{kind: stakeholder, ref: kickoff}}
    decided_by: Dana
    decided_on: {decided_on}
    revision: {revision}
{extra}"""


def assumption(id="A", valid_until="2027-12-31"):
    return ASSUMPTION.format(id=id, valid_until=valid_until)


def param(id="P", value="100", status="confirmed", origin="decided", mutability="build",
          decided_on="2026-11-04", revision=1, extra=""):
    return PARAM.format(id=id, value=value, status=status, origin=origin, mutability=mutability,
                        decided_on=decided_on, revision=revision, extra=extra)


MEASURED = ("    changeable_by: [measurement]\n"
            "    measurement: {{date: {date}, workload: A}}\n")


def data_doc(*, assumptions=(), parameters=(), datasets=(), rules=()):
    out = "app: t\n"
    for key, parts in (("assumptions", assumptions), ("parameters", parameters), ("datasets", datasets)):
        if parts:
            out += f"{key}:\n" + "".join(parts)
    return out + ("rules:\n" + "".join(rules) if rules else "rules: []\n")


def uses(rule_text, *, parameters="", assumptions="", datasets=""):
    inner = "".join(f"      {k}: [{v}]\n" for k, v in
                    (("parameters", parameters), ("assumptions", assumptions), ("datasets", datasets)) if v)
    return rule_text.replace("    scenarios:\n", f"    uses:\n{inner}    scenarios:\n", 1)


class ParameterTest(base.CheckerCase):
    def check(self, text, *args):
        return self.run_check(self.write(text), "--no-base", "--allow-unknown", *args)

    # --- references -------------------------------------------------------
    def test_valid_file_passes(self):
        text = data_doc(assumptions=[assumption()], parameters=[param()],
                        rules=[uses(rule(evidence=ev("passed")), parameters="P", assumptions="A")])
        code, out = self.check(text)
        self.assertEqual(code, 0, out)

    def test_rule_using_unknown_parameter_is_error(self):
        code, out = self.check(data_doc(rules=[uses(rule(), parameters="NOPE")]))
        self.assertEqual(code, 1)
        self.assertIn("uses unknown parameter NOPE", out)

    def test_id_reused_across_sections_is_error(self):
        code, out = self.check(data_doc(parameters=[param(id="X")], rules=[rule(id="X")]))
        self.assertEqual(code, 1)
        self.assertIn("X: id is used more than once", out)

    def test_parameter_with_unknown_assumption_is_error(self):
        code, out = self.check(data_doc(parameters=[param(extra="    assumptions: [GONE]\n")]))
        self.assertEqual(code, 1)
        self.assertIn("unknown assumption GONE", out)

    # --- confirmed parameters ---------------------------------------------
    def test_confirmed_parameter_needs_value(self):
        code, out = self.check(data_doc(parameters=[param(value="null")]))
        self.assertEqual(code, 1)
        self.assertIn("confirmed parameter has no value", out)

    def test_confirmed_parameter_needs_decider(self):
        text = data_doc(parameters=[param().replace("    decided_by: Dana\n", "")])
        code, out = self.check(text)
        self.assertEqual(code, 1)
        self.assertIn("missing decided_by", out)

    def test_inferred_source_cannot_be_confirmed(self):
        text = data_doc(parameters=[param().replace("kind: stakeholder", "kind: inferred")])
        code, out = self.check(text)
        self.assertEqual(code, 1)
        self.assertIn("source is missing or 'inferred'", out)

    def test_confirmed_measured_value_needs_measurement_date(self):
        code, out = self.check(data_doc(assumptions=[assumption()], parameters=[param(origin="measured")]))
        self.assertEqual(code, 1)
        self.assertIn("no measurement.date", out)

    # --- bounds -----------------------------------------------------------
    def test_value_outside_bounds_is_error(self):
        text = data_doc(parameters=[param(value="150", extra="    bounds: {min: 0, max: 100}\n")])
        code, out = self.check(text)
        self.assertEqual(code, 1)
        self.assertIn("above bounds.max 100", out)

    def test_runtime_number_without_bounds_warns(self):
        code, out = self.check(data_doc(parameters=[param(mutability="runtime")]))
        self.assertEqual(code, 0, out)
        self.assertIn("runtime numeric parameter has no bounds", out)

    # --- blocking and staleness -------------------------------------------
    def test_required_rule_with_unsettled_parameter_blocks(self):
        text = data_doc(parameters=[param(status="proposed", origin="estimated",
                                          extra="").replace("kind: stakeholder", "kind: inferred")],
                        rules=[uses(rule(evidence=ev("passed")), parameters="P")])
        p = self.write(text)
        self.assertEqual(self.run_check(p, "--no-base")[0], 3)
        code, out = self.run_check(p, "--no-base", "--allow-unknown")
        self.assertEqual(code, 0, out)
        self.assertIn("uses parameter P, which is not confirmed or has no value", out)

    def test_evidence_older_than_parameter_is_stale(self):
        text = data_doc(parameters=[param(decided_on="2026-12-01")],
                        rules=[uses(rule(evidence=ev("passed")), parameters="P")])
        code, out = self.check(text)
        self.assertIn("before parameter P was set (2026-12-01)", out)

    def test_expired_assumption_warns_for_rule_and_report(self):
        text = data_doc(assumptions=[assumption(valid_until="2026-12-31")],
                        rules=[uses(rule(evidence=ev("passed")), assumptions="A")])
        code, out = self.check(text, "--today", "2027-02-01")
        self.assertEqual(code, 0, out)
        self.assertIn("uses assumption A, which expired on 2026-12-31", out)
        self.assertIn("Expired assumptions or overdue reviews: A", out)
        code, out = self.check(text, "--today", "2026-12-01")
        self.assertNotIn("expired", out)

    def test_overdue_review_is_reported(self):
        text = data_doc(parameters=[param(extra="    review_by: 2026-12-01\n")])
        code, out = self.check(text, "--today", "2027-01-01")
        self.assertIn("review overdue since 2026-12-01", out)

    # --- weakening guard --------------------------------------------------
    def committed(self, text):
        p = self.write(text)
        self.init_repo(p)
        return p

    def test_changed_decided_value_needs_new_decision(self):
        p = self.committed(data_doc(parameters=[param(value="100")]))
        p.write_text(p.read_text().replace("value: 100", "value: 500"))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 1)
        self.assertIn("P: changed value since base", out)
        p.write_text(p.read_text().replace("revision: 1", "revision: 2"))
        self.assertEqual(self.run_check(p, "--allow-unknown")[0], 0)

    def test_relaxing_bounds_needs_new_decision(self):
        p = self.committed(data_doc(parameters=[param(extra="    bounds: {min: 0, max: 100}\n")]))
        p.write_text(p.read_text().replace("max: 100", "max: 900"))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 1)
        self.assertIn("changed bounds", out)

    def test_removed_confirmed_parameter_is_error(self):
        p = self.committed(data_doc(parameters=[param(id="P"), param(id="Q")]))
        p.write_text(data_doc(parameters=[param(id="P")]))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 1)
        self.assertIn("Q: confirmed parameter removed", out)

    def measured(self, value, date, changeable=True):
        extra = (MEASURED if changeable else "    measurement: {{date: {date}, workload: A}}\n")
        return data_doc(assumptions=[assumption()],
                        parameters=[param(value=value, origin="measured", extra=extra.format(date=date))])

    def test_measured_value_may_change_with_newer_measurement(self):
        p = self.committed(self.measured("400", "2026-11-04"))
        p.write_text(self.measured("430", "2026-11-10"))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 0, out)

    def test_measured_value_needs_a_newer_measurement_date(self):
        p = self.committed(self.measured("400", "2026-11-04"))
        p.write_text(self.measured("430", "2026-11-04"))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 1)
        self.assertIn("needs a newer measurement.date", out)

    def test_measured_value_without_changeable_by_needs_decision(self):
        p = self.committed(self.measured("400", "2026-11-04", changeable=False))
        p.write_text(self.measured("430", "2026-11-10", changeable=False))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 1)
        self.assertIn("P: changed value since base", out)

    def test_dropping_a_rules_parameter_link_is_guarded(self):
        text = data_doc(parameters=[param()], rules=[uses(rule(), parameters="P")])
        p = self.committed(text)
        p.write_text(data_doc(parameters=[param()], rules=[rule()]))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 1)
        self.assertIn("changed uses", out)


class ExportTest(base.CheckerCase):
    def export(self, text, *args):
        p = self.write(text)
        r = subprocess.run([sys.executable, "-W", "ignore", str(EXPORT), str(p), *args],
                           capture_output=True, text=True, cwd=self.dir)
        return r.returncode, r.stdout, r.stderr

    def test_json_export_includes_bounds_and_mutability(self):
        text = data_doc(parameters=[param(id="P-a", mutability="runtime",
                                          extra="    bounds: {min: 0, max: 200}\n"),
                                    param(id="P-b", value="7")])
        code, out, err = self.export(text)
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["parameters"]["P-a"]["bounds"], {"min": 0, "max": 200})
        self.assertEqual(data["parameters"]["P-b"]["mutability"], "build")

    def test_mutability_filter_and_flat_format(self):
        text = data_doc(parameters=[param(id="P-a", mutability="runtime",
                                          extra="    bounds: {min: 0, max: 200}\n"),
                                    param(id="P-b", value="7")])
        code, out, err = self.export(text, "--mutability", "build", "--format", "flat")
        self.assertEqual(json.loads(out), {"P-b": 7})

    def test_env_format(self):
        code, out, err = self.export(data_doc(parameters=[param(id="P-max-discount", value="15")]),
                                     "--format", "env")
        self.assertEqual(out.strip(), "P_MAX_DISCOUNT=15")

    def test_unsettled_parameters_are_refused_unless_requested(self):
        guess = param(id="G", status="proposed", origin="estimated").replace("kind: stakeholder", "kind: inferred")
        text = data_doc(parameters=[param(id="P"), guess])
        code, out, err = self.export(text, "--format", "flat")
        self.assertEqual(json.loads(out), {"P": 100})
        self.assertIn("skipped G", err)
        code, out, err = self.export(text, "--format", "flat", "--include-unsettled")
        self.assertEqual(json.loads(out), {"P": 100, "G": 100})

    def test_nothing_is_exported_when_the_file_has_errors(self):
        code, out, err = self.export(data_doc(parameters=[param(value="null")]))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Nothing exported", err)


if __name__ == "__main__":
    unittest.main()
