from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from dashboard.export import export_dashboard_data, handle_dashboard_cli
from minimizer.explain import explain_run
from policy.domain import classify_host, evaluate_domain_policy
from policy.rules import evaluate_httpx_request
from policy.yaml_loader import load_policy_with_source
from replay.renderer import replay_run


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


POLICY_YAML = """version: 1
mode: warn
domain_policy:
  allow_domains: ["api.example.com", "*.trusted.test"]
  deny_domains: ["evil.example.com", "*.malware.test"]
  warn_domains: ["*.unknown.test"]
  allow_localhost: true
  allow_private_networks: false
  warn_on_unknown_external: true
  block_on_deny: false
rules: []
"""


class DomainPolicyTest(unittest.TestCase):
    def _load_config(self) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "policy.yaml").write_text(POLICY_YAML, encoding="utf-8")
            policy, source = load_policy_with_source(root)
            dashboard_policy = handle_dashboard_cli(["policy"], root)
        self.assertEqual(source["type"], "yaml")
        self.assertEqual(dashboard_policy["domain_policy"]["deny_domains"], ["evil.example.com", "*.malware.test"])
        return policy["domain_policy"]

    def test_allow_deny_warn_and_wildcard_lists(self) -> None:
        config = self._load_config()
        allowed = evaluate_domain_policy("api.example.com", config)
        wildcard_allowed = evaluate_domain_policy("files.trusted.test", config)
        denied = evaluate_domain_policy("evil.example.com", config)
        wildcard_denied = evaluate_domain_policy("sub.malware.test", config)
        warned = evaluate_domain_policy("api.unknown.test", config)
        self.assertTrue(allowed["allowlisted"])
        self.assertTrue(wildcard_allowed["allowlisted"])
        self.assertEqual(denied["matched_domain_rule"], "domain_denylist_match")
        self.assertEqual(denied["domain_decision"], "deny")
        self.assertTrue(wildcard_denied["denylisted"])
        self.assertEqual(warned["matched_domain_rule"], "domain_warnlist_match")

    def test_unknown_external_policy(self) -> None:
        result = evaluate_domain_policy("unlisted.example.test", self._load_config())
        self.assertEqual(result["host_class"], "external")
        self.assertEqual(result["matched_domain_rule"], "domain_unknown_external")
        self.assertEqual(result["domain_decision"], "warn")

    def test_host_classification_without_dns(self) -> None:
        cases = {
            "localhost": "localhost",
            "127.0.0.1": "loopback",
            "::1": "loopback",
            "192.168.2.10": "private",
            "10.1.2.3": "private",
            "8.8.8.8": "ip",
            "example.test": "external",
            "": "unknown",
        }
        with patch("socket.getaddrinfo") as dns:
            for host, expected in cases.items():
                with self.subTest(host=host):
                    self.assertEqual(classify_host(host), expected)
            dns.assert_not_called()

    def test_http_rules_and_invalid_host_do_not_crash(self) -> None:
        deny = evaluate_httpx_request("GET", "https://evil.malware.test/path", scheme="https", host="evil.malware.test")
        insecure = evaluate_httpx_request("GET", "http://unlisted.example.test/path", scheme="http", host="unlisted.example.test")
        invalid = evaluate_httpx_request("GET", "<invalid-url>", scheme="", host="")
        self.assertEqual(deny["rule_id"], "domain_denylist_match")
        self.assertEqual(insecure["rule_id"], "insecure_http_request")
        self.assertEqual(insecure["domain_policy"]["matched_domain_rule"], "domain_unknown_external")
        self.assertEqual(invalid["domain_policy"]["host_class"], "unknown")

    def test_block_on_deny_uses_existing_http_enforcement(self) -> None:
        deny_rule = """rules:
  - id: domain_denylist_match
    match:
      event_type: network.http
      host:
        glob: "*.malware.test"
    risk_level: critical
    action: warn
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = POLICY_YAML.replace("block_on_deny: false", "block_on_deny: true").replace("rules: []", deny_rule)
            (root / "policy.yaml").write_text(policy, encoding="utf-8")
            with working_directory(root):
                denied = evaluate_httpx_request("GET", "https://evil.malware.test/path", scheme="https", host="evil.malware.test")
        self.assertEqual(denied["action"], "deny")
        self.assertEqual(denied["rule_id"], "domain_denylist_match")

    def test_yaml_missing_and_invalid_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy, source = load_policy_with_source(root)
            self.assertEqual(source["type"], "json_default")
            self.assertIn("domain_policy", policy)
            (root / "policy.yaml").write_text("version: [broken", encoding="utf-8")
            fallback, source = load_policy_with_source(root)
            self.assertEqual(source["type"], "yaml_error_fallback")
            self.assertIn("domain_policy", fallback)


class DomainPolicyIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-m", "traceseal", "run", "--", sys.executable, "examples/bad_agent_domain_policy.py"],
            cwd=cls.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"domain demo failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
        run_id = (cls.repo / "runs" / "latest").read_text(encoding="utf-8").strip()
        cls.run_dir = cls.repo / "runs" / run_id
        cls.events = [json.loads(line) for line in (cls.run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
        cls.http_events = [event for event in cls.events if event.get("type") == "network.http"]
        cls.cassette = [json.loads(line) for line in (cls.run_dir / "http_cassette.jsonl").read_text(encoding="utf-8").splitlines() if line]

    def _event(self, host: str) -> dict:
        return next(event for event in self.http_events if event["input"]["host"] == host)

    def test_demo_covers_domain_decisions_offline(self) -> None:
        self.assertEqual(len(self.http_events), 6)
        localhost = self._event("localhost")["risk"]["domain_policy"]
        loopback = self._event("127.0.0.1")["risk"]["domain_policy"]
        denied = self._event("evil.malware.test")["risk"]
        warned = self._event("api.unknown.test")["risk"]
        unknown = self._event("unlisted.example.test")["risk"]["domain_policy"]
        self.assertEqual(localhost["host_class"], "localhost")
        self.assertEqual(localhost["domain_decision"], "allow")
        self.assertEqual(loopback["host_class"], "loopback")
        self.assertEqual(denied["rule_id"], "domain_denylist_match")
        self.assertEqual(warned["rule_id"], "domain_warnlist_match")
        self.assertEqual(unknown["matched_domain_rule"], "domain_unknown_external")
        self.assertTrue(all(event["output"]["status"] == "ok" for event in self.http_events))

    def test_dashboard_replay_and_explain_show_domain_policy(self) -> None:
        dashboard = export_dashboard_data(self.run_dir)
        denied = next(event for event in dashboard["events"] if event.get("domain_policy", {}).get("denylisted"))
        denied_cassette = next(entry for entry in dashboard["http_cassette"]["entries"] if entry["host"] == "evil.malware.test")
        self.assertEqual(denied["domain_policy"]["domain_decision"], "deny")
        self.assertEqual(denied["risk"]["suggested_policy"], 'deny http host "*.malware.test"')
        self.assertEqual(denied_cassette["matched_domain_rule"], "domain_denylist_match")
        replay = replay_run(self.run_dir)
        explanation = explain_run(self.run_dir)
        self.assertIn("域名策略", replay)
        self.assertIn("domain_decision: deny", explanation)
        self.assertIn("domain_denylist_match", explanation)

    def test_cassette_domain_metadata_is_redacted(self) -> None:
        denied = next(entry for entry in self.cassette if entry["host"] == "evil.malware.test")
        self.assertEqual(denied["domain_decision"], "deny")
        self.assertEqual(denied["matched_domain_rule"], "domain_denylist_match")
        self.assertEqual(denied["domain_policy"]["host_class"], "external")
        serialized = json.dumps(self.cassette, ensure_ascii=False)
        self.assertNotIn("synthetic-domain-demo", serialized)
        self.assertNotIn("Bearer", serialized)
        self.assertNotIn("content", denied["request_body_summary"])


if __name__ == "__main__":
    unittest.main()
