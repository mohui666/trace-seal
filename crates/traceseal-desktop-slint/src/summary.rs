use serde_json::Value;

const UNAVAILABLE: &str = "Unavailable";
const NO_RISKS: &str = "No risks";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BridgeStatusKind {
    MockFallback,
    Loaded,
    CommandFailed,
    NoRunsFound,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DashboardSummary {
    pub data_source: String,
    pub latest_run_id: String,
    pub latest_status: String,
    pub event_count: i32,
    pub risk_count: i32,
    pub policy_summary: String,
    pub started_at: String,
    pub finished_at: String,
    pub run_title: String,
    pub workspace: String,
    pub run_policy_mode: String,
    pub risk_summary: String,
    pub bridge_status: BridgeStatusKind,
    pub last_error: String,
}

impl DashboardSummary {
    pub fn mock() -> Self {
        Self {
            data_source: "mock fallback".to_string(),
            latest_run_id: "mock-run-0001".to_string(),
            latest_status: "mock".to_string(),
            event_count: 12,
            risk_count: 3,
            policy_summary: "mock / read-only".to_string(),
            started_at: UNAVAILABLE.to_string(),
            finished_at: UNAVAILABLE.to_string(),
            run_title: "Mock run".to_string(),
            workspace: UNAVAILABLE.to_string(),
            run_policy_mode: "mock / read-only".to_string(),
            risk_summary: UNAVAILABLE.to_string(),
            bridge_status: BridgeStatusKind::MockFallback,
            last_error: "none".to_string(),
        }
    }

    pub fn command_failed(message: impl Into<String>) -> Self {
        let mut summary = Self::mock();
        summary.data_source = "dashboard-data".to_string();
        summary.bridge_status = BridgeStatusKind::CommandFailed;
        summary.last_error = clean_text(&message.into());
        summary
    }

    pub fn no_runs_found(message: impl Into<String>) -> Self {
        Self {
            data_source: "dashboard-data".to_string(),
            latest_run_id: "no runs".to_string(),
            latest_status: "empty".to_string(),
            event_count: 0,
            risk_count: 0,
            policy_summary: "not loaded".to_string(),
            started_at: UNAVAILABLE.to_string(),
            finished_at: UNAVAILABLE.to_string(),
            run_title: UNAVAILABLE.to_string(),
            workspace: UNAVAILABLE.to_string(),
            run_policy_mode: UNAVAILABLE.to_string(),
            risk_summary: UNAVAILABLE.to_string(),
            bridge_status: BridgeStatusKind::NoRunsFound,
            last_error: clean_text(&message.into()),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SummaryError {
    message: String,
}

impl SummaryError {
    pub fn summary(&self) -> String {
        self.message.clone()
    }
}

impl From<serde_json::Error> for SummaryError {
    fn from(error: serde_json::Error) -> Self {
        Self {
            message: clean_text(&format!("invalid dashboard-data JSON: {error}")),
        }
    }
}

pub fn parse_latest_summary(json: &str) -> Result<DashboardSummary, SummaryError> {
    let payload: Value = serde_json::from_str(json)?;
    if let Some(error) = dashboard_error(&payload) {
        if error.contains("RUN_NOT_FOUND") {
            return Ok(DashboardSummary::no_runs_found(error));
        }
        return Err(SummaryError { message: error });
    }

    Ok(DashboardSummary {
        data_source: "dashboard-data latest".to_string(),
        latest_run_id: string_field(&payload, &["run_id"])
            .unwrap_or_else(|| "unknown run".to_string()),
        latest_status: string_field(&payload, &["status"]).unwrap_or_else(|| "unknown".to_string()),
        event_count: int_field(&payload, &["event_count"]).unwrap_or(0),
        risk_count: int_field(&payload, &["high_risk_count", "risk_count"]).unwrap_or(0),
        policy_summary: policy_source_summary(payload.get("policy_source"))
            .unwrap_or_else(|| "policy not loaded".to_string()),
        started_at: string_field(&payload, &["started_at"]).unwrap_or_else(unavailable),
        finished_at: string_field(&payload, &["finished_at"]).unwrap_or_else(unavailable),
        run_title: payload
            .get("summary")
            .and_then(|summary| string_field(summary, &["title"]))
            .unwrap_or_else(unavailable),
        workspace: payload
            .get("summary")
            .and_then(|summary| string_field(summary, &["workspace"]))
            .unwrap_or_else(unavailable),
        run_policy_mode: payload
            .get("summary")
            .and_then(|summary| string_field(summary, &["policy_mode"]))
            .unwrap_or_else(unavailable),
        risk_summary: risk_summary(payload.get("risks")),
        bridge_status: BridgeStatusKind::Loaded,
        last_error: "none".to_string(),
    })
}

pub fn parse_run_list_summary(json: &str) -> Result<DashboardSummary, SummaryError> {
    let payload: Value = serde_json::from_str(json)?;
    if let Some(error) = dashboard_error(&payload) {
        return Err(SummaryError { message: error });
    }

    let runs = payload.get("runs").and_then(Value::as_array);
    let Some(runs) = runs else {
        return Ok(DashboardSummary::no_runs_found(
            "dashboard-data list returned no runs array",
        ));
    };
    let Some(first) = runs.first() else {
        return Ok(DashboardSummary::no_runs_found(
            "dashboard-data list returned no runs",
        ));
    };

    Ok(DashboardSummary {
        data_source: format!("dashboard-data list ({})", runs.len()),
        latest_run_id: string_field(first, &["run_id"])
            .unwrap_or_else(|| "unknown run".to_string()),
        latest_status: string_field(first, &["status"]).unwrap_or_else(|| "unknown".to_string()),
        event_count: int_field(first, &["event_count"]).unwrap_or(0),
        risk_count: int_field(first, &["high_risk_count", "risk_count"]).unwrap_or(0),
        policy_summary: "not loaded".to_string(),
        started_at: string_field(first, &["started_at"]).unwrap_or_else(unavailable),
        finished_at: string_field(first, &["finished_at"]).unwrap_or_else(unavailable),
        run_title: UNAVAILABLE.to_string(),
        workspace: UNAVAILABLE.to_string(),
        run_policy_mode: UNAVAILABLE.to_string(),
        risk_summary: UNAVAILABLE.to_string(),
        bridge_status: BridgeStatusKind::Loaded,
        last_error: "none".to_string(),
    })
}

pub fn parse_policy_summary(json: &str) -> Result<DashboardSummary, SummaryError> {
    let payload: Value = serde_json::from_str(json)?;
    if let Some(error) = dashboard_error(&payload) {
        return Err(SummaryError { message: error });
    }

    let rule_count = payload
        .get("rules")
        .and_then(Value::as_array)
        .map(|rules| rules.len())
        .unwrap_or(0);
    let source = policy_source_summary(payload.get("policy_source"))
        .unwrap_or_else(|| "policy source unknown".to_string());

    Ok(DashboardSummary {
        data_source: "dashboard-data policy".to_string(),
        latest_run_id: "unchanged".to_string(),
        latest_status: "policy loaded".to_string(),
        event_count: 0,
        risk_count: 0,
        policy_summary: format!("{rule_count} rules / {source}"),
        started_at: UNAVAILABLE.to_string(),
        finished_at: UNAVAILABLE.to_string(),
        run_title: UNAVAILABLE.to_string(),
        workspace: UNAVAILABLE.to_string(),
        run_policy_mode: UNAVAILABLE.to_string(),
        risk_summary: UNAVAILABLE.to_string(),
        bridge_status: BridgeStatusKind::Loaded,
        last_error: "none".to_string(),
    })
}

fn dashboard_error(payload: &Value) -> Option<String> {
    if payload.get("ok").and_then(Value::as_bool) != Some(false) {
        return None;
    }
    let error = payload.get("error")?;
    let code = string_field(error, &["code"]).unwrap_or_else(|| "COMMAND_FAILED".to_string());
    let message =
        string_field(error, &["message"]).unwrap_or_else(|| "dashboard-data failed".to_string());
    Some(clean_text(&format!("{code}: {message}")))
}

fn policy_source_summary(value: Option<&Value>) -> Option<String> {
    let value = value?;
    if value.is_null() {
        return None;
    }
    if let Some(text) = value.as_str() {
        return Some(clean_text(text));
    }
    let source_type = string_field(value, &["type"]).unwrap_or_else(|| "unknown".to_string());
    let path = string_field(value, &["path", "name"]);
    Some(match path {
        Some(path) if !path.is_empty() => format!("{source_type} / {}", clean_text(&path)),
        _ => source_type,
    })
}

fn risk_summary(value: Option<&Value>) -> String {
    let Some(risks) = value.and_then(Value::as_array) else {
        return UNAVAILABLE.to_string();
    };
    let Some(first) = risks.first() else {
        return NO_RISKS.to_string();
    };

    let level = string_field(first, &["level"]).unwrap_or_else(unavailable);
    let kind = string_field(first, &["kind"]).unwrap_or_else(unavailable);
    let message = string_field(first, &["message"]).unwrap_or_else(unavailable);
    format!("{level} / {kind} / {message}")
}

fn string_field(value: &Value, fields: &[&str]) -> Option<String> {
    fields
        .iter()
        .filter_map(|field| value.get(*field))
        .find_map(|value| match value {
            Value::String(text) => Some(clean_text(text)),
            Value::Number(number) => Some(number.to_string()),
            Value::Bool(flag) => Some(flag.to_string()),
            _ => None,
        })
}

fn int_field(value: &Value, fields: &[&str]) -> Option<i32> {
    fields
        .iter()
        .filter_map(|field| value.get(*field))
        .find_map(|value| value.as_i64())
        .map(|number| number.clamp(i32::MIN as i64, i32::MAX as i64) as i32)
}

fn unavailable() -> String {
    UNAVAILABLE.to_string()
}

fn clean_text(text: &str) -> String {
    let collapsed = text.split_whitespace().collect::<Vec<_>>().join(" ");
    collapsed.chars().take(240).collect()
}

#[cfg(test)]
mod tests {
    use super::{
        parse_latest_summary, parse_policy_summary, parse_run_list_summary, BridgeStatusKind,
    };

    #[test]
    fn parse_latest_extracts_run_counts_and_status() {
        let summary = parse_latest_summary(
            r#"{
                "run_id": "run_20260623_120000_000000",
                "status": "completed",
                "event_count": 7,
                "high_risk_count": 2,
                "policy_source": {"type": "yaml", "path": "policy.yaml"}
            }"#,
        )
        .expect("latest summary should parse");

        assert_eq!(summary.latest_run_id, "run_20260623_120000_000000");
        assert_eq!(summary.latest_status, "completed");
        assert_eq!(summary.event_count, 7);
        assert_eq!(summary.risk_count, 2);
        assert_eq!(summary.policy_summary, "yaml / policy.yaml");
        assert_eq!(summary.started_at, "Unavailable");
        assert_eq!(summary.finished_at, "Unavailable");
        assert_eq!(summary.run_title, "Unavailable");
        assert_eq!(summary.workspace, "Unavailable");
        assert_eq!(summary.run_policy_mode, "Unavailable");
        assert_eq!(summary.risk_summary, "Unavailable");
        assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
    }

    #[test]
    fn parse_latest_uses_fallbacks_for_missing_fields() {
        let summary = parse_latest_summary(r#"{"schema_version":1}"#)
            .expect("missing fields should still produce a conservative summary");

        assert_eq!(summary.latest_run_id, "unknown run");
        assert_eq!(summary.latest_status, "unknown");
        assert_eq!(summary.event_count, 0);
        assert_eq!(summary.risk_count, 0);
        assert_eq!(summary.started_at, "Unavailable");
        assert_eq!(summary.finished_at, "Unavailable");
        assert_eq!(summary.run_title, "Unavailable");
        assert_eq!(summary.workspace, "Unavailable");
        assert_eq!(summary.run_policy_mode, "Unavailable");
        assert_eq!(summary.risk_summary, "Unavailable");
    }

    #[test]
    fn malformed_json_returns_error() {
        let error = parse_latest_summary("{bad json").expect_err("malformed JSON must be an error");
        assert!(error.summary().contains("invalid dashboard-data JSON"));
    }

    #[test]
    fn run_list_empty_returns_no_runs_state() {
        let summary = parse_run_list_summary(r#"{"schema_version":1,"runs":[]}"#)
            .expect("empty list is a valid empty state");

        assert_eq!(summary.bridge_status, BridgeStatusKind::NoRunsFound);
        assert_eq!(summary.latest_run_id, "no runs");
    }

    #[test]
    fn policy_summary_counts_rules() {
        let summary = parse_policy_summary(
            r#"{
                "schema_version": 1,
                "policy_source": {"type": "default_json"},
                "rules": [{"rule_id":"dangerous_delete"},{"rule_id":"env_write"}]
            }"#,
        )
        .expect("policy summary should parse");

        assert_eq!(summary.policy_summary, "2 rules / default_json");
        assert_eq!(summary.bridge_status, BridgeStatusKind::Loaded);
    }

    #[test]
    fn run_not_found_error_maps_to_empty_state() {
        let summary = parse_latest_summary(
            r#"{"ok":false,"error":{"code":"RUN_NOT_FOUND","message":"latest run pointer does not exist"}}"#,
        )
        .expect("RUN_NOT_FOUND should become an empty state");

        assert_eq!(summary.bridge_status, BridgeStatusKind::NoRunsFound);
        assert!(summary.last_error.contains("RUN_NOT_FOUND"));
    }
}
