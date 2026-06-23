#[allow(dead_code)]
#[path = "../src/dashboard_data.rs"]
mod dashboard_data;

#[allow(dead_code)]
#[path = "../src/summary.rs"]
mod summary;

use dashboard_data::{command_args, python_executable, DashboardCommand};
use summary::{
    parse_latest_summary, parse_policy_summary, parse_run_list_summary, BridgeStatusKind,
};

fn fixed_commands() -> [(DashboardCommand, &'static [&'static str]); 3] {
    [
        (
            DashboardCommand::Latest,
            &["-m", "traceseal", "dashboard-data", "latest"],
        ),
        (
            DashboardCommand::List,
            &["-m", "traceseal", "dashboard-data", "list"],
        ),
        (
            DashboardCommand::Policy,
            &["-m", "traceseal", "dashboard-data", "policy"],
        ),
    ]
}

#[test]
fn fixed_dashboard_commands_match_python_module_contract() {
    assert_eq!(python_executable(), "python");

    for (command, expected_args) in fixed_commands() {
        assert_eq!(command_args(command), expected_args);
    }
}

#[test]
fn fixed_dashboard_commands_exclude_mutating_or_interactive_subcommands() {
    let forbidden_exact = [
        "run",
        "replay",
        "explain",
        "cmd",
        "/c",
        "powershell",
        "-Command",
        "sh",
        "-c",
    ];
    let forbidden_fragments = ["cmd /c", "powershell -Command", "sh -c"];

    for (command, _) in fixed_commands() {
        let args = command_args(command);
        let joined = args.join(" ");

        assert!(!forbidden_exact.iter().any(|value| args.contains(value)));
        assert!(!forbidden_fragments
            .iter()
            .any(|fragment| joined.contains(fragment)));
    }
}

#[test]
fn fixed_dashboard_commands_have_no_shell_metacharacters_or_user_slots() {
    let shell_metacharacters = [";", "&", "|", ">", "<", "`", "$(", "&&", "||"];
    let user_input_slots = ["{", "}", "<run_id>", "run_id", "selector", "workspace"];

    for (command, _) in fixed_commands() {
        let args = command_args(command);

        assert!(args
            .iter()
            .all(|arg| !shell_metacharacters.iter().any(|token| arg.contains(token))));
        assert!(args
            .iter()
            .all(|arg| !user_input_slots.iter().any(|slot| arg.contains(slot))));
    }
}

#[test]
fn command_boundary_tests_do_not_execute_python_core() {
    for (command, _) in fixed_commands() {
        let args = command_args(command);
        assert_eq!(args[0], "-m");
        assert_eq!(args[1], "traceseal");
        assert_eq!(args[2], "dashboard-data");
    }
}

#[test]
fn parser_accepts_valid_latest_json_fixture() {
    let summary = parse_latest_summary(
        r#"{
            "schema_version": 1,
            "run_id": "run_20260623_120000_000000",
            "status": "completed",
            "event_count": 42,
            "high_risk_count": 5,
            "policy_source": {"type": "yaml", "path": "policy.yaml"}
        }"#,
    )
    .expect("valid latest fixture should parse");

    assert_eq!(summary.data_source, "dashboard-data latest");
    assert_eq!(summary.latest_run_id, "run_20260623_120000_000000");
    assert_eq!(summary.latest_status, "completed");
    assert_eq!(summary.event_count, 42);
    assert_eq!(summary.risk_count, 5);
    assert_eq!(summary.policy_summary, "yaml / policy.yaml");
    assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
    assert_eq!(summary.last_error, "none");
}

#[test]
fn parser_accepts_valid_policy_json_fixture() {
    let summary = parse_policy_summary(
        r#"{
            "schema_version": 1,
            "policy_source": {"type": "default_json"},
            "rules": [
                {"rule_id": "dangerous_delete"},
                {"rule_id": "env_write"},
                {"rule_id": "git_push"}
            ]
        }"#,
    )
    .expect("valid policy fixture should parse");

    assert_eq!(summary.data_source, "dashboard-data policy");
    assert_eq!(summary.latest_run_id, "unchanged");
    assert_eq!(summary.latest_status, "policy loaded");
    assert_eq!(summary.policy_summary, "3 rules / default_json");
    assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
}

#[test]
fn parser_maps_empty_list_json_to_no_runs_state() {
    let summary = parse_run_list_summary(r#"{"schema_version":1,"runs":[]}"#)
        .expect("empty list fixture should parse");

    assert_eq!(summary.bridge_status, BridgeStatusKind::NoRunsFound);
    assert_eq!(summary.data_source, "dashboard-data");
    assert_eq!(summary.latest_run_id, "no runs");
    assert_eq!(summary.latest_status, "empty");
    assert_eq!(summary.event_count, 0);
    assert_eq!(summary.risk_count, 0);
}

#[test]
fn parser_uses_missing_field_fallbacks_without_panicking() {
    let latest = parse_latest_summary(r#"{"schema_version":1}"#).expect("missing fields are valid");
    let list = parse_run_list_summary(r#"{"schema_version":1,"runs":[{"run_id":"run_minimal"}]}"#)
        .expect("minimal run list is valid");

    assert_eq!(latest.latest_run_id, "unknown run");
    assert_eq!(latest.latest_status, "unknown");
    assert_eq!(latest.event_count, 0);
    assert_eq!(latest.risk_count, 0);
    assert_eq!(latest.policy_summary, "policy not loaded");

    assert_eq!(list.latest_run_id, "run_minimal");
    assert_eq!(list.latest_status, "unknown");
    assert_eq!(list.event_count, 0);
    assert_eq!(list.risk_count, 0);
}

#[test]
fn parser_falls_back_for_event_and_risk_count_type_mismatches() {
    let summary = parse_latest_summary(
        r#"{
            "schema_version": 1,
            "run_id": "run_bad_counts",
            "status": "completed",
            "event_count": "not-a-number",
            "high_risk_count": null
        }"#,
    )
    .expect("type mismatches should still produce a conservative summary");

    assert_eq!(summary.event_count, 0);
    assert_eq!(summary.risk_count, 0);
}

#[test]
fn parser_falls_back_for_policy_rule_count_and_source() {
    let summary = parse_policy_summary(r#"{"schema_version":1,"rules":"not-a-list"}"#)
        .expect("policy fallback should parse");

    assert_eq!(summary.policy_summary, "0 rules / policy source unknown");
    assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
}

#[test]
fn malformed_json_returns_error_without_panicking_or_leaking_environment() {
    let error = parse_latest_summary(
        r#"{"schema_version":1,"message":"PATH=C:\\secret;USERPROFILE=C:\\Users\\demo""#,
    )
    .expect_err("malformed JSON should return an error");
    let summary = error.summary();

    assert!(summary.contains("invalid dashboard-data JSON"));
    assert!(!summary.contains("PATH="));
    assert!(!summary.contains("USERPROFILE="));
    assert!(!summary.contains("C:\\Users\\demo"));
}
