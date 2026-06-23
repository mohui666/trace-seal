use serde_json::Value;
use std::fs;
use std::path::PathBuf;

fn fixture_path(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures/dashboard-data")
        .join(name)
}

fn read_fixture(name: &str) -> Value {
    let path = fixture_path(name);

    assert!(
        path.is_file(),
        "dashboard-data fixture must exist: {}",
        path.display()
    );

    let text = fs::read_to_string(&path)
        .unwrap_or_else(|err| panic!("failed to read fixture {}: {}", path.display(), err));
    serde_json::from_str(&text)
        .unwrap_or_else(|err| panic!("failed to parse fixture {}: {}", path.display(), err))
}

#[test]
fn latest_fixture_has_slint_contract_fields() {
    let value = read_fixture("latest.json");

    assert_eq!(value["schema_version"].as_i64(), Some(1));
    assert!(value["run_id"].as_str().is_some());
    assert!(value["status"].as_str().is_some());
    assert!(value["event_count"].as_i64().is_some());
    assert!(value["risk_count"].as_i64().is_some());
    assert!(value["summary"].is_object());
}

#[test]
fn list_fixture_has_slint_contract_fields() {
    let value = read_fixture("list.json");

    assert_eq!(value["schema_version"].as_i64(), Some(1));

    let runs = value["runs"].as_array().expect("runs must be an array");
    assert!(
        !runs.is_empty(),
        "runs fixture must include at least one run"
    );

    let first = &runs[0];
    assert!(first["run_id"].as_str().is_some());
    assert!(first["status"].as_str().is_some());
    assert!(first["event_count"].as_i64().is_some());
    assert!(first["risk_count"].as_i64().is_some());
}

#[test]
fn policy_fixture_has_slint_contract_fields() {
    let value = read_fixture("policy.json");

    assert_eq!(value["schema_version"].as_i64(), Some(1));
    assert!(value["policy"].is_object());
    assert!(value["policy"]["mode"].as_str().is_some());

    let rules = value["rules"].as_array().expect("rules must be an array");
    assert!(
        !rules.is_empty(),
        "policy fixture must include at least one rule"
    );

    let first = &rules[0];
    assert!(first["id"].as_str().is_some());
    assert!(first["decision"].as_str().is_some());
}
