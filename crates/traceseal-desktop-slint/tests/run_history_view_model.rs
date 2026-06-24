#[allow(dead_code)]
#[path = "../src/dashboard_data.rs"]
mod dashboard_data;

#[allow(dead_code)]
#[path = "../src/summary.rs"]
mod summary;

use std::fs;
use std::path::PathBuf;

use dashboard_data::read_demo_fixture_bundle;
use summary::{
    parse_demo_fixture_summary, parse_run_history_rows, parse_run_list_summary, BridgeStatusKind,
};

fn fixture_path(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures/dashboard-data")
        .join(name)
}

fn read_fixture(name: &str) -> String {
    let path = fixture_path(name);
    fs::read_to_string(&path)
        .unwrap_or_else(|err| panic!("failed to read fixture {}: {}", path.display(), err))
}

#[test]
fn list_fixture_maps_to_run_history_rows() {
    let fixture = read_fixture("list.json");
    let rows = parse_run_history_rows(&fixture).expect("list fixture should parse");

    assert!(
        !rows.is_empty(),
        "list fixture should include at least one run history row"
    );

    let first = &rows[0];
    assert_eq!(first.run_id, "fixture-run-001");
    assert_eq!(first.status, "completed");
    assert_eq!(first.started_at, "2026-01-01T00:00:00Z");
    assert_eq!(first.event_count, 3);
    assert_eq!(first.risk_count, 1);
}

#[test]
fn run_list_summary_carries_history_rows_for_ui() {
    let fixture = read_fixture("list.json");
    let summary = parse_run_list_summary(&fixture).expect("list fixture should parse");

    assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
    assert_eq!(summary.latest_run_id, "fixture-run-001");
    assert_eq!(summary.latest_status, "completed");
    assert_eq!(summary.event_count, 3);
    assert_eq!(summary.risk_count, 1);
    assert_eq!(summary.run_history.len(), 1);
    assert_eq!(summary.run_history[0].run_id, "fixture-run-001");
}

#[test]
fn empty_list_produces_empty_history_without_panicking() {
    let rows =
        parse_run_history_rows(r#"{"schema_version":1,"runs":[]}"#).expect("empty list parses");
    let summary = parse_run_list_summary(r#"{"schema_version":1,"runs":[]}"#)
        .expect("empty list summary parses");

    assert!(rows.is_empty());
    assert!(summary.run_history.is_empty());
    assert_eq!(summary.bridge_status, BridgeStatusKind::NoRunsFound);
    assert_eq!(summary.latest_run_id, "no runs");
}

#[test]
fn demo_fixture_preview_uses_list_history_row() {
    let bundle = read_demo_fixture_bundle().expect("demo fixtures should be readable");
    let summary =
        parse_demo_fixture_summary(&bundle.latest_json, &bundle.list_json, &bundle.policy_json)
            .expect("demo fixture summary should parse");

    assert_eq!(summary.bridge_status, BridgeStatusKind::DemoFixture);
    assert_eq!(summary.run_history.len(), 1);

    let first = &summary.run_history[0];
    assert_eq!(first.run_id, "fixture-run-001");
    assert_eq!(first.status, "completed");
    assert_eq!(first.event_count, 3);
    assert_eq!(first.risk_count, 1);
}

#[test]
fn missing_optional_run_history_fields_use_safe_fallbacks() {
    let rows = parse_run_history_rows(
        r#"{
            "schema_version": 1,
            "runs": [{"run_id": "minimal-run"}]
        }"#,
    )
    .expect("minimal run history payload should parse");

    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0].run_id, "minimal-run");
    assert_eq!(rows[0].status, "unknown");
    assert_eq!(rows[0].started_at, "Unavailable");
    assert_eq!(rows[0].event_count, 0);
    assert_eq!(rows[0].risk_count, 0);
}
