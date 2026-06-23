#[allow(dead_code)]
#[path = "../src/summary.rs"]
mod summary;

use std::fs;
use std::path::PathBuf;

use summary::{parse_latest_summary, BridgeStatusKind};

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
fn latest_fixture_maps_to_run_detail_fields() {
    let fixture = read_fixture("latest.json");
    let summary = parse_latest_summary(&fixture).expect("latest fixture should parse");

    assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
    assert_eq!(summary.latest_run_id, "fixture-run-001");
    assert_eq!(summary.latest_status, "completed");
    assert_eq!(summary.started_at, "2026-01-01T00:00:00Z");
    assert_eq!(summary.finished_at, "2026-01-01T00:00:05Z");
    assert_eq!(summary.event_count, 3);
    assert_eq!(summary.risk_count, 1);
    assert_eq!(summary.run_title, "Fixture run");
    assert_eq!(summary.workspace, "<fixture-workspace>");
    assert_eq!(summary.run_policy_mode, "dry-run");
    assert_eq!(
        summary.risk_summary,
        "medium / process.spawn / fixture risk"
    );
}

#[test]
fn missing_optional_run_detail_fields_do_not_panic() {
    let summary = parse_latest_summary(
        r#"{
            "schema_version": 1,
            "run_id": "run_minimal",
            "status": "completed",
            "event_count": 1,
            "risk_count": 0
        }"#,
    )
    .expect("minimal latest payload should parse");

    assert_eq!(summary.latest_run_id, "run_minimal");
    assert_eq!(summary.started_at, "Unavailable");
    assert_eq!(summary.finished_at, "Unavailable");
    assert_eq!(summary.run_title, "Unavailable");
    assert_eq!(summary.workspace, "Unavailable");
    assert_eq!(summary.run_policy_mode, "Unavailable");
    assert_eq!(summary.risk_summary, "Unavailable");
}
