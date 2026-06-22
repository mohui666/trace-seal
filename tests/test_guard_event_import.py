from __future__ import annotations

import copy
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from dashboard.export import export_dashboard_data
from minimizer.explain import explain_run
from replay.renderer import replay_run
from traceseal.guard_import import (
    GUARD_ARTIFACT_NAME,
    GuardImportError,
    get_guard_event_summary,
    import_guard_events,
    load_imported_guard_events,
    main,
    maybe_find_guard_events,
)
from traceseal.guard_schema import load_guard_events


class GuardEventImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = Path(__file__).parent / "fixtures"
        cls.health = load_guard_events(cls.fixtures / "guard_health.jsonl")[0]
        cls.spawn = load_guard_events(cls.fixtures / "guard_process_spawn.jsonl")[0]

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_dir = self.root / "run_import_test"
        self.run_dir.mkdir()
        self.manifest = {
            "schema_version": 1,
            "run_id": self.run_dir.name,
            "command": ["python", "agent.py"],
            "command_display": "python agent.py",
            "status": "completed",
            "exit_code": 0,
        }
        self._write_manifest(self.manifest)
        (self.run_dir / "events.jsonl").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_manifest(self, manifest: dict) -> None:
        (self.run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def _source(self, name: str, events: list[dict], *, blank_lines: bool = False) -> Path:
        path = self.root / name
        lines = [json.dumps(event, ensure_ascii=False, separators=(",", ":")) for event in events]
        separator = "\n\n" if blank_lines else "\n"
        path.write_text(separator.join(lines) + "\n", encoding="utf-8")
        return path

    def test_imports_guard_health_artifact_and_manifest_metadata(self) -> None:
        result = import_guard_events(
            self.run_dir, self.fixtures / "guard_health.jsonl"
        )
        artifact = self.run_dir / GUARD_ARTIFACT_NAME
        self.assertTrue(artifact.is_file())
        self.assertEqual(result["guard_event_count"], 1)
        self.assertEqual(result["guard_event_types"], ["guard.health"])
        manifest = json.loads((self.run_dir / "manifest.json").read_text("utf-8"))
        self.assertEqual(manifest["guard"], result)
        self.assertEqual(manifest["command_display"], "python agent.py")

    def test_imports_process_spawn_without_executing_target(self) -> None:
        marker = self.root / "TARGET_MUST_NOT_EXIST.txt"
        event = copy.deepcopy(self.spawn)
        event["process"]["command_line"] = [
            "python",
            "-c",
            f"from pathlib import Path; Path({str(marker)!r}).write_text('executed')",
        ]
        source = self._source("spawn.jsonl", [event])
        result = import_guard_events(self.run_dir, source)
        imported = load_imported_guard_events(self.run_dir)
        self.assertEqual(result["guard_event_types"], ["process.spawn"])
        self.assertIs(imported[0]["metadata"]["executed"], False)
        self.assertFalse(marker.exists())

    def test_mixed_import_preserves_source_order_and_has_deterministic_types(self) -> None:
        result = import_guard_events(
            self.run_dir, self.fixtures / "guard_mixed_events.jsonl"
        )
        imported = load_imported_guard_events(self.run_dir)
        self.assertEqual(
            [event["event_type"] for event in imported],
            ["guard.health", "process.spawn"],
        )
        self.assertEqual(
            result["guard_event_types"], ["guard.health", "process.spawn"]
        )
        self.assertEqual(get_guard_event_summary(self.run_dir), result)

    def test_unknown_but_valid_event_type_is_preserved(self) -> None:
        event = copy.deepcopy(self.health)
        event["event_id"] = "guard_evt_future_000001"
        event["event_type"] = "future.generic"
        source = self._source("future.jsonl", [event])
        result = import_guard_events(self.run_dir, source)
        self.assertEqual(result["guard_event_types"], ["future.generic"])
        self.assertEqual(
            load_imported_guard_events(self.run_dir)[0]["event_type"],
            "future.generic",
        )

    def test_old_run_without_guard_metadata_remains_compatible(self) -> None:
        self.assertIsNone(maybe_find_guard_events(self.run_dir))
        self.assertEqual(load_imported_guard_events(self.run_dir), [])
        self.assertEqual(get_guard_event_summary(self.run_dir)["guard_event_count"], 0)
        self.assertIn("TraceSeal 执行时间线回放", replay_run(self.run_dir))
        self.assertIn("未发现有害工具调用", explain_run(self.run_dir))
        dashboard = export_dashboard_data(self.run_dir)
        self.assertEqual(dashboard["event_count"], 0)
        self.assertNotIn("guard", dashboard)

    def test_replay_explain_and_dashboard_ignore_optional_guard_metadata(self) -> None:
        import_guard_events(self.run_dir, self.fixtures / "guard_mixed_events.jsonl")
        self.assertIn("事件数量: 0", replay_run(self.run_dir))
        self.assertIn("未发现有害工具调用", explain_run(self.run_dir))
        self.assertNotIn("guard", export_dashboard_data(self.run_dir))

        manifest = json.loads((self.run_dir / "manifest.json").read_text("utf-8"))
        manifest["guard"] = {"guard_events_path": "../outside.jsonl", "invalid": True}
        self._write_manifest(manifest)
        self.assertIn("TraceSeal 执行时间线回放", replay_run(self.run_dir))
        self.assertIn("未发现有害工具调用", explain_run(self.run_dir))

        (self.run_dir / GUARD_ARTIFACT_NAME).write_text(
            "{malformed optional Guard artifact}\n", encoding="utf-8"
        )
        manifest["guard"] = {"guard_events_path": GUARD_ARTIFACT_NAME}
        self._write_manifest(manifest)
        self.assertIn("TraceSeal 执行时间线回放", replay_run(self.run_dir))
        self.assertIn("未发现有害工具调用", explain_run(self.run_dir))
        self.assertNotIn("guard", export_dashboard_data(self.run_dir))

    def test_invalid_schema_and_missing_required_field_are_rejected_atomically(self) -> None:
        cases = []
        wrong_version = copy.deepcopy(self.health)
        wrong_version["schema_version"] = "guard.event.v2"
        cases.append((wrong_version, "schema_version"))
        missing_policy = copy.deepcopy(self.health)
        del missing_policy["policy"]
        cases.append((missing_policy, "missing required field"))

        for index, (event, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                source = self._source(f"invalid-{index}.jsonl", [event])
                with self.assertRaisesRegex(GuardImportError, expected):
                    import_guard_events(self.run_dir, source)
                self.assertFalse((self.run_dir / GUARD_ARTIFACT_NAME).exists())
                manifest = json.loads(
                    (self.run_dir / "manifest.json").read_text("utf-8")
                )
                self.assertNotIn("guard", manifest)

    def test_malformed_jsonl_has_clear_error(self) -> None:
        source = self.root / "malformed.jsonl"
        source.write_text("\n{broken json}\n", encoding="utf-8")
        with self.assertRaisesRegex(GuardImportError, "line 2"):
            import_guard_events(self.run_dir, source)

    def test_blank_lines_are_skipped(self) -> None:
        source = self._source(
            "blank-lines.jsonl", [self.health, self.spawn], blank_lines=True
        )
        result = import_guard_events(self.run_dir, source)
        self.assertEqual(result["guard_event_count"], 2)

    def test_duplicate_ids_are_rejected_and_out_of_order_input_is_preserved(self) -> None:
        duplicate = copy.deepcopy(self.spawn)
        duplicate["event_id"] = self.health["event_id"]
        source = self._source("duplicate.jsonl", [self.health, duplicate])
        with self.assertRaisesRegex(GuardImportError, "duplicate Guard event_id"):
            import_guard_events(self.run_dir, source)

        out_of_order_health = copy.deepcopy(self.health)
        out_of_order_health["event_id"] = "guard_evt_order_2"
        out_of_order_health["timestamp"] = "2026-06-22T00:00:02.000000Z"
        out_of_order_spawn = copy.deepcopy(self.spawn)
        out_of_order_spawn["event_id"] = "guard_evt_order_1"
        out_of_order_spawn["timestamp"] = "2026-06-22T00:00:01.000000Z"
        source = self._source(
            "out-of-order.jsonl", [out_of_order_health, out_of_order_spawn]
        )
        import_guard_events(self.run_dir, source)
        self.assertEqual(
            [event["event_id"] for event in load_imported_guard_events(self.run_dir)],
            ["guard_evt_order_2", "guard_evt_order_1"],
        )

    def test_non_null_run_id_must_match_target_run(self) -> None:
        event = copy.deepcopy(self.health)
        event["run_id"] = "another-run"
        source = self._source("wrong-run.jsonl", [event])
        with self.assertRaisesRegex(GuardImportError, "does not match"):
            import_guard_events(self.run_dir, source)

    def test_refuses_to_overwrite_existing_imported_artifact(self) -> None:
        import_guard_events(self.run_dir, self.fixtures / "guard_health.jsonl")
        with self.assertRaisesRegex(GuardImportError, "refusing to overwrite"):
            import_guard_events(
                self.run_dir, self.fixtures / "guard_process_spawn.jsonl"
            )

    def test_module_cli_reports_success_and_missing_source(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            status = main(
                [
                    "--run",
                    str(self.run_dir),
                    "--guard-events",
                    str(self.fixtures / "guard_health.jsonl"),
                ]
            )
        self.assertEqual(status, 0)
        self.assertIn("imported 1 Guard event", stdout.getvalue())

        other_run = self.root / "other-run"
        other_run.mkdir()
        stderr = StringIO()
        with redirect_stderr(stderr):
            status = main(
                [
                    "--run",
                    str(other_run),
                    "--guard-events",
                    str(self.root / "missing.jsonl"),
                ]
            )
        self.assertEqual(status, 2)
        self.assertIn("does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
