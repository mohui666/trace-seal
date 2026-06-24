#[allow(dead_code)]
#[path = "../src/summary.rs"]
mod summary;

use std::fs;
use std::path::PathBuf;

use summary::{parse_latest_summary, BridgeStatusKind, DashboardLoadState, DashboardSummary};

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
fn initial_state_is_loading() {
    let state = DashboardLoadState::loading("Loading dashboard data...");

    assert!(state.is_loading);
    assert!(!state.has_error);
    assert!(!state.has_data);
    assert_eq!(state.loading_message, "Loading dashboard data...");
    assert_eq!(state.status_message, "Loading dashboard data...");
}

#[test]
fn successful_load_maps_to_loaded_state() {
    let state = DashboardLoadState::loaded("Dashboard data loaded");

    assert!(!state.is_loading);
    assert!(!state.has_error);
    assert!(state.has_data);
    assert_eq!(state.status_message, "Dashboard data loaded");
}

#[test]
fn command_failure_maps_to_error_state() {
    let summary = DashboardSummary::command_failed("dashboard-data command failed");
    let state = DashboardLoadState::error(format!(
        "Failed to load dashboard data: {}",
        summary.last_error
    ));

    assert_eq!(summary.bridge_status, BridgeStatusKind::CommandFailed);
    assert!(!state.is_loading);
    assert!(state.has_error);
    assert!(!state.has_data);
    assert!(state
        .error_message
        .contains("Failed to load dashboard data"));
    assert!(state
        .error_message
        .contains("dashboard-data command failed"));
}

#[test]
fn run_detail_fields_remain_available_after_loaded_state() {
    let fixture = read_fixture("latest.json");
    let summary = parse_latest_summary(&fixture).expect("latest fixture should parse");
    let state = DashboardLoadState::loaded("Dashboard data loaded");

    assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
    assert!(state.has_data);
    assert_eq!(summary.latest_run_id, "fixture-run-001");
    assert_eq!(summary.started_at, "2026-01-01T00:00:00Z");
    assert_eq!(summary.finished_at, "2026-01-01T00:00:05Z");
    assert_eq!(summary.run_title, "Fixture run");
    assert_eq!(summary.workspace, "<fixture-workspace>");
    assert_eq!(summary.run_policy_mode, "dry-run");
}
