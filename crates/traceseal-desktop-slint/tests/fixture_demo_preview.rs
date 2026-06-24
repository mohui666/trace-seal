#[allow(dead_code)]
#[path = "../src/dashboard_data.rs"]
mod dashboard_data;

#[allow(dead_code)]
#[path = "../src/summary.rs"]
mod summary;

use dashboard_data::read_demo_fixture_bundle;
use summary::{parse_demo_fixture_summary, BridgeStatusKind};

#[test]
fn demo_fixture_bundle_reads_latest_list_and_policy() {
    let bundle = read_demo_fixture_bundle().expect("demo fixtures should be readable");

    assert!(bundle.latest_json.contains("fixture-run-001"));
    assert!(bundle.list_json.contains("\"runs\""));
    assert!(bundle.policy_json.contains("dry-run"));
}

#[test]
fn demo_fixture_summary_maps_expected_preview_fields() {
    let bundle = read_demo_fixture_bundle().expect("demo fixtures should be readable");
    let summary =
        parse_demo_fixture_summary(&bundle.latest_json, &bundle.list_json, &bundle.policy_json)
            .expect("demo fixture summary should parse");

    assert_eq!(summary.bridge_status, BridgeStatusKind::DemoFixture);
    assert!(summary.data_source.contains("demo fixture"));
    assert!(summary.data_source.contains("latest/list/policy"));
    assert_eq!(summary.latest_run_id, "fixture-run-001");
    assert_eq!(summary.latest_status, "completed");
    assert_eq!(summary.event_count, 3);
    assert_eq!(summary.risk_count, 1);
    assert_eq!(summary.run_policy_mode, "dry-run");
    assert!(summary.policy_summary.contains("dry-run"));
    assert_eq!(
        summary.risk_summary,
        "medium / process.spawn / fixture risk"
    );
}

#[test]
fn demo_fixture_summary_uses_list_and_policy_fallbacks_without_panicking() {
    let summary = parse_demo_fixture_summary(
        r#"{"schema_version":1}"#,
        r#"{
            "schema_version": 1,
            "runs": [{
                "run_id": "fallback-run",
                "status": "completed",
                "event_count": 3,
                "risk_count": 1
            }]
        }"#,
        r#"{
            "schema_version": 1,
            "policy": {"mode": "dry-run"},
            "rules": []
        }"#,
    )
    .expect("missing demo fields should still produce a conservative summary");

    assert_eq!(summary.bridge_status, BridgeStatusKind::DemoFixture);
    assert_eq!(summary.latest_run_id, "fallback-run");
    assert_eq!(summary.latest_status, "completed");
    assert_eq!(summary.event_count, 3);
    assert_eq!(summary.risk_count, 1);
    assert_eq!(summary.run_policy_mode, "dry-run");
    assert_eq!(summary.risk_summary, "Unavailable");
}

#[test]
fn demo_fixture_summary_missing_fields_keep_safe_defaults() {
    let summary = parse_demo_fixture_summary(
        r#"{"schema_version":1}"#,
        r#"{"schema_version":1,"runs":[{}]}"#,
        r#"{"schema_version":1}"#,
    )
    .expect("minimal demo payloads should parse without panicking");

    assert_eq!(summary.bridge_status, BridgeStatusKind::DemoFixture);
    assert_eq!(summary.latest_run_id, "unknown run");
    assert_eq!(summary.latest_status, "unknown");
    assert_eq!(summary.event_count, 0);
    assert_eq!(summary.risk_count, 0);
    assert_eq!(summary.run_policy_mode, "Unavailable");
    assert_eq!(summary.policy_summary, "0 rules / policy source unknown");
}
