from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from traceseal.guard_schema import (
    GuardEventParseError,
    GuardEventValidationError,
    load_guard_events,
    validate_guard_event,
    validate_guard_health_event,
)


class GuardHealthSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_path = Path(__file__).parent / "fixtures" / "guard_health.jsonl"
        cls.fixture = load_guard_events(cls.fixture_path)[0]

    def test_valid_guard_health_event(self) -> None:
        validated = validate_guard_health_event(self.fixture)
        self.assertEqual(validated["schema_version"], "guard.event.v1")
        self.assertEqual(validated["event_type"], "guard.health")
        self.assertEqual(validated["guard"]["mode"], "observe")

    def test_missing_required_field_fails(self) -> None:
        event = copy.deepcopy(self.fixture)
        del event["policy"]
        with self.assertRaisesRegex(GuardEventValidationError, "missing required field.*policy"):
            validate_guard_event(event)

    def test_wrong_schema_version_fails(self) -> None:
        event = copy.deepcopy(self.fixture)
        event["schema_version"] = "guard.event.v2"
        with self.assertRaisesRegex(GuardEventValidationError, "schema_version"):
            validate_guard_event(event)

    def test_wrong_event_type_fails_health_validation(self) -> None:
        event = copy.deepcopy(self.fixture)
        event["event_type"] = "process.spawn"
        with self.assertRaisesRegex(GuardEventValidationError, "event_type"):
            validate_guard_health_event(event)

    def test_invalid_enums_fail(self) -> None:
        cases = (
            (("risk_level",), "severe", "risk_level"),
            (("policy", "decision"), "block", "policy.decision"),
            (("redaction", "status"), "none", "redaction.status"),
        )
        for path, value, expected in cases:
            with self.subTest(path=path):
                event = copy.deepcopy(self.fixture)
                target = event
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaisesRegex(GuardEventValidationError, expected):
                    validate_guard_event(event)

    def test_jsonl_multiple_lines_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "guard_events.jsonl"
            line = json.dumps(self.fixture, separators=(",", ":"))
            artifact.write_text(f"\n{line}\n\n{line}\n", encoding="utf-8")
            events = load_guard_events(artifact)
        self.assertEqual(len(events), 2)
        for event in events:
            validate_guard_health_event(event)

    def test_invalid_json_reports_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "guard_events.jsonl"
            artifact.write_text("\n{broken json}\n", encoding="utf-8")
            with self.assertRaisesRegex(GuardEventParseError, "line 2"):
                load_guard_events(artifact)

    def test_missing_guard_artifact_is_an_unaffected_old_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_run = Path(tmp) / "run_without_guard_metadata"
            old_run.mkdir()
            self.assertEqual(load_guard_events(old_run / "guard_events.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
