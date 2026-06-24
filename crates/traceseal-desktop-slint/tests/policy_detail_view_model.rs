#[allow(dead_code)]
#[path = "../src/dashboard_data.rs"]
mod dashboard_data;

#[allow(dead_code)]
#[path = "../src/summary.rs"]
mod summary;

use std::fs;
use std::path::PathBuf;

use dashboard_data::read_demo_fixture_bundle;
use summary::{parse_demo_fixture_summary, parse_policy_summary, BridgeStatusKind};

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
fn policy_fixture_maps_to_policy_detail_fields() {
    let fixture = read_fixture("policy.json");
    let summary = parse_policy_summary(&fixture).expect("policy fixture should parse");

    assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
    assert_eq!(summary.policy_detail.mode, "dry-run");
    assert_eq!(summary.policy_detail.source, "fixture-policy.yaml");
    assert_eq!(summary.policy_detail.rule_count, 2);
    assert_eq!(summary.policy_detail.rules.len(), 2);

    let first = &summary.policy_detail.rules[0];
    assert_eq!(first.rule_id, "fixture.process_spawn");
    assert_eq!(first.decision, "warn");

    let second = &summary.policy_detail.rules[1];
    assert_eq!(second.rule_id, "fixture.git_push");
    assert_eq!(second.decision, "allow");
}

#[test]
fn empty_rules_produce_empty_policy_detail_without_panicking() {
    let summary = parse_policy_summary(
        r#"{
            "schema_version": 1,
            "policy": {
                "mode": "dry-run",
                "source": "empty-policy.yaml",
                "rule_count": 0
            },
            "rules": []
        }"#,
    )
    .expect("empty rules should still produce a policy detail view model");

    assert_eq!(summary.policy_detail.mode, "dry-run");
    assert_eq!(summary.policy_detail.source, "empty-policy.yaml");
    assert_eq!(summary.policy_detail.rule_count, 0);
    assert!(summary.policy_detail.rules.is_empty());
}

#[test]
fn missing_optional_policy_fields_use_safe_fallbacks() {
    let summary = parse_policy_summary(
        r#"{
            "schema_version": 1,
            "rules": [{}]
        }"#,
    )
    .expect("missing policy fields should not panic");

    assert_eq!(summary.policy_detail.mode, "Unavailable");
    assert_eq!(summary.policy_detail.source, "Unavailable");
    assert_eq!(summary.policy_detail.rule_count, 1);
    assert_eq!(summary.policy_detail.rules.len(), 1);
    assert_eq!(summary.policy_detail.rules[0].rule_id, "unknown rule");
    assert_eq!(summary.policy_detail.rules[0].decision, "unknown");
}

#[test]
fn demo_fixture_preview_carries_policy_detail_fields() {
    let bundle = read_demo_fixture_bundle().expect("demo fixtures should be readable");
    let summary =
        parse_demo_fixture_summary(&bundle.latest_json, &bundle.list_json, &bundle.policy_json)
            .expect("demo fixture summary should parse");

    assert_eq!(summary.bridge_status, BridgeStatusKind::DemoFixture);
    assert_eq!(summary.policy_detail.mode, "dry-run");
    assert_eq!(summary.policy_detail.source, "fixture-policy.yaml");
    assert_eq!(summary.policy_detail.rule_count, 2);
    assert_eq!(summary.policy_detail.rules.len(), 2);
    assert_eq!(
        summary.policy_detail.rules[0].rule_id,
        "fixture.process_spawn"
    );
    assert_eq!(summary.policy_detail.rules[0].decision, "warn");
    assert_eq!(summary.policy_detail.rules[1].rule_id, "fixture.git_push");
    assert_eq!(summary.policy_detail.rules[1].decision, "allow");
}
