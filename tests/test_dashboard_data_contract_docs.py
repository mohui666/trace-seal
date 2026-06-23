from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs" / "dashboard-data-contract.md"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "dashboard-data"
FIXTURES = {
    "latest": FIXTURE_DIR / "latest.json",
    "list": FIXTURE_DIR / "list.json",
    "policy": FIXTURE_DIR / "policy.json",
}
README = ROOT / "README.md"
DOCS_README = ROOT / "docs" / "README.md"
PROJECT_STATUS = ROOT / "docs" / "project-status.md"


class DashboardDataContractDocsTest(unittest.TestCase):
    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def read_json(self, path: Path) -> dict[str, object]:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIsInstance(data, dict)
        return data

    def test_contract_doc_exists(self) -> None:
        self.assertTrue(CONTRACT_DOC.exists(), "missing docs/dashboard-data-contract.md")

    def test_dashboard_data_fixtures_exist_and_are_valid_json(self) -> None:
        for name, path in FIXTURES.items():
            with self.subTest(name=name):
                self.assertTrue(path.exists(), f"missing fixture {path.relative_to(ROOT)}")
                self.read_json(path)

    def test_latest_fixture_contains_core_fields(self) -> None:
        payload = self.read_json(FIXTURES["latest"])
        for field in ("schema_version", "run_id", "status", "event_count", "risk_count"):
            with self.subTest(field=field):
                self.assertIn(field, payload)

    def test_list_fixture_contains_core_fields(self) -> None:
        payload = self.read_json(FIXTURES["list"])
        for field in ("schema_version", "runs"):
            with self.subTest(field=field):
                self.assertIn(field, payload)
        self.assertIsInstance(payload["runs"], list)

    def test_policy_fixture_contains_core_fields(self) -> None:
        payload = self.read_json(FIXTURES["policy"])
        for field in ("schema_version", "policy", "rules"):
            with self.subTest(field=field):
                self.assertIn(field, payload)
        self.assertIsInstance(payload["rules"], list)

    def test_contract_doc_records_shared_read_only_boundaries(self) -> None:
        text = self.read_text(CONTRACT_DOC)
        required_terms = [
            "dashboard-data latest",
            "dashboard-data list",
            "dashboard-data policy",
            "Electron remains the default",
            "Slint remains experimental-only",
            "does not require either desktop path to call `traceseal run`",
            "Electron 仍是默认桌面实现",
            "Slint 仍是实验用途",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_core_docs_link_dashboard_data_contract(self) -> None:
        for path in (README, DOCS_README, PROJECT_STATUS):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("docs/dashboard-data-contract.md", self.read_text(path))

    def test_contract_docs_avoid_misleading_assertions(self) -> None:
        combined = "\n".join(
            [
                self.read_text(CONTRACT_DOC),
                self.read_text(README),
                self.read_text(DOCS_README),
                self.read_text(PROJECT_STATUS),
            ]
        )
        forbidden_phrases = [
            "Slint has replaced Electron",
            "Electron has been replaced",
            "Slint is the default desktop",
            "Stage 5 is complete",
            "v0.3.1 released",
            "dashboard-data contract requires traceseal run",
        ]
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
