"""Regression tests for check_rules.py. Run:

    python3 -m unittest discover tools/business-rules/tests
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "check_rules.py"
EXAMPLE = SKILL / "templates" / "rules.example.json"

RULE = """\
  - id: {id}
    statement: {statement}
    status: confirmed
    revision: {revision}
    required: {required}
    source: {{kind: stakeholder, ref: kickoff}}
    decided_by: Dana
    decided_on: {decided_on}
    depends_on: {depends_on}
    scenarios:
      - {{kind: required, name: works, given: g, when: w, then: {then}}}
      - {{kind: forbidden, name: refused, given: g, when: w, then: refused}}
    check: {{method: test, ref: t.py, strength: bounded}}
{evidence}"""


def rule(id="R", statement="s", revision=1, required="true", decided_on="2026-11-04",
         depends_on="[]", then="done", evidence=""):
    return RULE.format(id=id, statement=statement, revision=revision, required=required,
                       decided_on=decided_on, depends_on=depends_on, then=then, evidence=evidence)


def doc(*rules):
    return "app: t\nrules:\n" + "".join(rules)


def ev(result, extra=""):
    return f"    evidence: {{result: {result}, ref: r, date: 2026-11-04{extra}}}\n"


class CheckerCase(unittest.TestCase):
    """Helpers shared by the checker test classes; has no tests of its own."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write(self, text, name="rules.yaml"):
        p = self.dir / name
        p.write_text(text)
        return p

    def run_check(self, path, *args, env=None):
        e = dict(os.environ, **(env or {}))
        r = subprocess.run([sys.executable, "-W", "ignore", str(SCRIPT), str(path), *args],
                           capture_output=True, text=True, env=e, cwd=self.dir)
        return r.returncode, r.stdout + r.stderr

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.dir, check=True, capture_output=True)

    def init_repo(self, path):
        self.git("init", "-q")
        self.git("config", "user.email", "t@t")
        self.git("config", "user.name", "t")
        self.git("add", path.name)
        self.git("commit", "-qm", "base")


class CheckerTest(CheckerCase):
    # --- exit codes -------------------------------------------------------
    def test_example_passes(self):
        code, out = self.run_check(EXAMPLE, "--no-base")
        self.assertEqual(code, 0, out)

    def test_structural_error_exits_1(self):
        p = self.write(doc(rule() + "    extra_field: nope\n"))
        self.assertEqual(self.run_check(p, "--no-base")[0], 1)

    def test_confirmed_needs_required_flag(self):
        p = self.write(doc(rule().replace("    required: true\n", "")))
        code, out = self.run_check(p, "--no-base")
        self.assertEqual(code, 1)
        self.assertIn("'required'", out)

    def test_unmeasurable_needs_reason(self):
        p = self.write(doc(rule(evidence="    evidence: {result: unmeasurable}\n")))
        code, out = self.run_check(p, "--no-base")
        self.assertEqual(code, 1)
        self.assertIn("no evidence.reason", out)

    def test_failed_rule_exits_2(self):
        p = self.write(doc(rule(evidence=ev("failed"))))
        self.assertEqual(self.run_check(p, "--no-base")[0], 2)

    def test_unknown_required_blocks_unless_allowed(self):
        p = self.write(doc(rule()))
        self.assertEqual(self.run_check(p, "--no-base")[0], 3)
        self.assertEqual(self.run_check(p, "--no-base", "--allow-unknown")[0], 0)

    def test_unmeasurable_required_blocks(self):
        p = self.write(doc(rule(evidence="    evidence: {result: unmeasurable, reason: subjective}\n")))
        self.assertEqual(self.run_check(p, "--no-base")[0], 3)

    def test_optional_unknown_does_not_block(self):
        p = self.write(doc(rule(required="false")))
        self.assertEqual(self.run_check(p, "--no-base")[0], 0)

    # --- warnings ---------------------------------------------------------
    def test_stale_evidence_warns(self):
        p = self.write(doc(rule(evidence="    evidence: {result: passed, ref: r, date: 2026-01-01}\n")))
        code, out = self.run_check(p, "--no-base")
        self.assertEqual(code, 0)
        self.assertIn("stale evidence", out)

    def test_stale_rule_revision_warns(self):
        e = ev("passed", ", provenance: {rule_revision: '1'}")
        p = self.write(doc(rule(revision=2, evidence=e)))
        self.assertIn("revision 1", self.run_check(p, "--no-base")[1])

    # --- dependencies -----------------------------------------------------
    def test_failed_dependency_downgrades_pass(self):
        p = self.write(doc(rule(id="A", evidence=ev("failed")),
                           rule(id="B", depends_on="[A]", evidence=ev("passed"))))
        code, out = self.run_check(p, "--no-base")
        self.assertEqual(code, 2, out)  # A failed
        self.assertIn("downgraded to unknown: dependency A failed", out)
        p2 = self.write(doc(rule(id="A", required="false", evidence=ev("failed")),
                            rule(id="B", depends_on="[A]", evidence=ev("passed"))), "b.yaml")
        code, out = self.run_check(p2, "--no-base", "--allow-unknown")
        self.assertEqual(code, 2)
        self.assertIn("B (dependency A failed)", out)

    def test_downgrade_blocks_required_rule(self):
        # A is failed but optional-to-block logic still reports failure; use JSON to inspect B.
        p = self.write(doc(rule(id="A", evidence=ev("failed")),
                           rule(id="B", depends_on="[A]", evidence=ev("passed"))))
        code, out = self.run_check(p, "--no-base", "--json")
        self.assertIn('"blocked_unchecked": [\n      "B"', out)

    def test_weak_dependency_warns_only(self):
        p = self.write(doc(rule(id="A"), rule(id="B", depends_on="[A]", evidence=ev("passed"))))
        code, out = self.run_check(p, "--no-base", "--allow-unknown")
        self.assertEqual(code, 0, out)
        self.assertIn("dependency A is not confirmed and passed", out)

    def test_dependency_cycle_is_error(self):
        p = self.write(doc(rule(id="A", depends_on="[B]"), rule(id="B", depends_on="[A]")))
        code, out = self.run_check(p, "--no-base")
        self.assertEqual(code, 1)
        self.assertIn("dependency cycle", out)

    def test_unconfirmed_proxy_does_not_resolve(self):
        unm = rule(id="U", required="true",
                   evidence="    evidence: {result: unmeasurable, reason: r, proxies: [P]}\n")
        prox = "  - {id: P, statement: proxy, status: proposed}\n"
        p = self.write(doc(unm, prox))
        code, out = self.run_check(p, "--no-base")
        self.assertEqual(code, 3)
        self.assertIn("proxy P is not confirmed yet", out)

    # --- weakening guard --------------------------------------------------
    def test_weakening_detected_by_default_and_cleared_by_revision(self):
        p = self.write(doc(rule(evidence=ev("passed"))))
        self.init_repo(p)
        self.assertEqual(self.run_check(p)[0], 0)  # unchanged vs HEAD
        p.write_text(p.read_text().replace("then: done", "then: anything"))
        code, out = self.run_check(p)
        self.assertEqual(code, 1)
        self.assertIn("without a newer decided_on or higher revision", out)
        self.assertEqual(self.run_check(p, "--no-base")[0], 0)  # guard can be disabled
        p.write_text(p.read_text().replace("revision: 1", "revision: 2"))
        self.assertEqual(self.run_check(p)[0], 0)

    def test_newer_decided_on_also_clears(self):
        p = self.write(doc(rule(evidence=ev("passed"))))
        self.init_repo(p)
        p.write_text(p.read_text().replace("then: done", "then: other")
                     .replace("decided_on: 2026-11-04", "decided_on: 2026-11-05"))
        self.assertEqual(self.run_check(p)[0], 0)

    def test_removed_confirmed_rule_is_error(self):
        p = self.write(doc(rule(id="A"), rule(id="B")))
        self.init_repo(p)
        p.write_text(doc(rule(id="A")))
        code, out = self.run_check(p, "--allow-unknown")
        self.assertEqual(code, 1)
        self.assertIn("B: confirmed rule removed", out)

    def test_untracked_file_skips_guard_quietly(self):
        p = self.write(doc(rule(evidence=ev("passed"))))
        code, out = self.run_check(p)
        self.assertEqual(code, 0, out)
        self.assertNotIn("weakening", out)

    def test_explicit_bad_ref_warns_and_skips(self):
        p = self.write(doc(rule(evidence=ev("passed"))))
        self.init_repo(p)
        code, out = self.run_check(p, "--base", "nosuchref")
        self.assertEqual(code, 0, out)
        self.assertIn("weakening check skipped", out)

    # --- shape checks -----------------------------------------------------
    def test_missing_jsonschema_fails_unless_skipped(self):
        stub = self.dir / "stub"
        stub.mkdir()
        (stub / "jsonschema.py").write_text("raise ImportError('hidden for test')\n")
        p = self.write(doc(rule(evidence=ev("passed"))))
        env = {"PYTHONPATH": str(stub)}
        code, out = self.run_check(p, "--no-base", env=env)
        self.assertEqual(code, 1)
        self.assertIn("--skip-shape", out)
        code, out = self.run_check(p, "--no-base", "--skip-shape", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("shape checks skipped", out)


if __name__ == "__main__":
    unittest.main()
