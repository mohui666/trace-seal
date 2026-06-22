from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from traceseal.guard_schema import (
    GuardEventValidationError,
    load_guard_events,
    validate_guard_health_event,
    validate_guard_process_spawn_event,
)


class GuardProcessSpawnSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixtures = Path(__file__).parent / "fixtures"
        cls.fixture_path = fixtures / "guard_process_spawn.jsonl"
        cls.fixture = load_guard_events(cls.fixture_path)[0]
        cls.health_fixture_path = fixtures / "guard_health.jsonl"

    def test_valid_process_spawn_event(self) -> None:
        validated = validate_guard_process_spawn_event(self.fixture)
        self.assertEqual(validated["schema_version"], "guard.event.v1")
        self.assertEqual(validated["event_type"], "process.spawn")
        self.assertEqual(validated["process"]["process_name"], "python")
        self.assertIs(validated["metadata"]["dry_run"], True)
        self.assertIs(validated["metadata"]["executed"], False)

    def test_missing_required_envelope_field_fails(self) -> None:
        event = copy.deepcopy(self.fixture)
        del event["policy"]
        with self.assertRaisesRegex(GuardEventValidationError, "missing required field.*policy"):
            validate_guard_process_spawn_event(event)

    def test_wrong_schema_version_fails(self) -> None:
        event = copy.deepcopy(self.fixture)
        event["schema_version"] = "guard.event.v2"
        with self.assertRaisesRegex(GuardEventValidationError, "schema_version"):
            validate_guard_process_spawn_event(event)

    def test_wrong_event_type_fails(self) -> None:
        event = copy.deepcopy(self.fixture)
        event["event_type"] = "guard.health"
        with self.assertRaisesRegex(GuardEventValidationError, "event_type"):
            validate_guard_process_spawn_event(event)

    def test_process_fields_are_required_and_consistent(self) -> None:
        cases = (
            ("process_name", None, "process.process_name"),
            ("cwd", None, "process.cwd"),
            ("command_line", [], "process.command_line"),
            ("command_line", ["node", "example.py"], "must match"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                event = copy.deepcopy(self.fixture)
                event["process"][field] = value
                with self.assertRaisesRegex(GuardEventValidationError, expected):
                    validate_guard_process_spawn_event(event)

    def test_process_object_requires_contract_keys(self) -> None:
        event = copy.deepcopy(self.fixture)
        del event["process"]["parent_pid"]
        with self.assertRaisesRegex(GuardEventValidationError, "parent_pid"):
            validate_guard_process_spawn_event(event)

    def test_dry_run_never_claims_execution(self) -> None:
        event = copy.deepcopy(self.fixture)
        event["metadata"]["executed"] = True
        with self.assertRaisesRegex(GuardEventValidationError, "executed must be false"):
            validate_guard_process_spawn_event(event)

        event = copy.deepcopy(self.fixture)
        event["metadata"]["dry_run"] = False
        with self.assertRaisesRegex(GuardEventValidationError, "dry_run must be true"):
            validate_guard_process_spawn_event(event)

    def test_invalid_enums_fail(self) -> None:
        cases = (
            (("risk_level",), "severe", "risk_level"),
            (("policy", "decision"), "block", "policy.decision"),
            (("redaction", "status"), "not_required", "redaction.status"),
        )
        for path, value, expected in cases:
            with self.subTest(path=path):
                event = copy.deepcopy(self.fixture)
                target = event
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaisesRegex(GuardEventValidationError, expected):
                    validate_guard_process_spawn_event(event)

    def test_jsonl_multiple_lines_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "guard_events.jsonl"
            line = json.dumps(self.fixture, separators=(",", ":"))
            artifact.write_text(f"\n{line}\n\n{line}\n", encoding="utf-8")
            events = load_guard_events(artifact)
        self.assertEqual(len(events), 2)
        for event in events:
            validate_guard_process_spawn_event(event)

    def test_fixture_contains_no_plaintext_secret(self) -> None:
        fixture_text = self.fixture_path.read_text(encoding="utf-8")
        self.assertNotIn("token=secret", fixture_text)
        self.assertIn("token=<redacted>", fixture_text)
        self.assertEqual(self.fixture["redaction"]["status"], "redacted")

    def test_guard_health_fixture_still_validates(self) -> None:
        health = load_guard_events(self.health_fixture_path)[0]
        validate_guard_health_event(health)


if __name__ == "__main__":
    unittest.main()
