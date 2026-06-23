use std::{cell::Cell, rc::Rc};

mod dashboard_data;
mod summary;

use dashboard_data::{run_dashboard_command, BridgeError, DashboardCommand};
use summary::{
    parse_latest_summary, parse_policy_summary, parse_run_list_summary, BridgeStatusKind,
    DashboardSummary,
};

slint::include_modules!();

#[derive(Clone, Copy, PartialEq, Eq)]
enum Language {
    English,
    Chinese,
}

fn status_text(language: Language, status: BridgeStatusKind) -> &'static str {
    match (language, status) {
        (Language::English, BridgeStatusKind::MockFallback) => "mock fallback",
        (Language::English, BridgeStatusKind::Loaded) => "loaded from dashboard-data",
        (Language::English, BridgeStatusKind::CommandFailed) => "command failed",
        (Language::English, BridgeStatusKind::NoRunsFound) => "no runs found",
        (Language::Chinese, BridgeStatusKind::MockFallback) => "mock 兜底",
        (Language::Chinese, BridgeStatusKind::Loaded) => "已从 dashboard-data 加载",
        (Language::Chinese, BridgeStatusKind::CommandFailed) => "命令失败",
        (Language::Chinese, BridgeStatusKind::NoRunsFound) => "未找到运行记录",
    }
}

fn apply_summary(ui: &AppWindow, summary: &DashboardSummary, language: Language) {
    ui.set_data_source(summary.data_source.clone().into());
    ui.set_latest_run(summary.latest_run_id.clone().into());
    ui.set_latest_status(summary.latest_status.clone().into());
    ui.set_event_count(summary.event_count);
    ui.set_risk_count(summary.risk_count);
    ui.set_policy_mode(summary.policy_summary.clone().into());
    ui.set_bridge_status(status_text(language, summary.bridge_status).into());
    ui.set_last_error(summary.last_error.clone().into());
}

fn apply_policy_summary(ui: &AppWindow, summary: &DashboardSummary, language: Language) {
    ui.set_data_source(summary.data_source.clone().into());
    ui.set_policy_mode(summary.policy_summary.clone().into());
    ui.set_bridge_status(status_text(language, summary.bridge_status).into());
    ui.set_last_error(summary.last_error.clone().into());
}

fn apply_language(ui: &AppWindow, language: Language, status: BridgeStatusKind) {
    match language {
        Language::English => {
            ui.set_title_text("TraceSeal Slint Read-only Spike".into());
            ui.set_subtitle_text("Experimental dashboard-data bridge only".into());
            ui.set_bridge_title_text("Read-only dashboard-data bridge".into());
            ui.set_data_source_label("Data source".into());
            ui.set_bridge_status_label("Bridge status".into());
            ui.set_latest_run_label("Latest run".into());
            ui.set_latest_status_label("Latest status".into());
            ui.set_event_count_label("Event count".into());
            ui.set_risk_count_label("Risk count".into());
            ui.set_policy_mode_label("Policy summary".into());
            ui.set_last_error_label("Last error".into());
            ui.set_boundary_text(
                "Read-only spike: Electron remains default. Uses only fixed Python Core dashboard-data commands. No traceseal run, target commands, workspace writes, policy edits, packaging changes, release changes, or Stage 5 promotion.".into(),
            );
            ui.set_load_latest_text("Load latest".into());
            ui.set_load_policy_text("Load policy".into());
            ui.set_load_run_list_text("Load run list summary".into());
            ui.set_toggle_language_text("中文".into());
        }
        Language::Chinese => {
            ui.set_title_text("TraceSeal Slint 只读实验窗口".into());
            ui.set_subtitle_text("仅实验用途的 dashboard-data 桥接".into());
            ui.set_bridge_title_text("只读 dashboard-data 桥接".into());
            ui.set_data_source_label("数据来源".into());
            ui.set_bridge_status_label("桥接状态".into());
            ui.set_latest_run_label("最新运行".into());
            ui.set_latest_status_label("最新状态".into());
            ui.set_event_count_label("事件数量".into());
            ui.set_risk_count_label("风险数量".into());
            ui.set_policy_mode_label("策略摘要".into());
            ui.set_last_error_label("最近错误".into());
            ui.set_boundary_text(
                "只读实验：Electron 仍是默认桌面实现。仅使用固定 Python Core dashboard-data 命令。不调用 traceseal run、不执行目标命令、不写入 workspace、不编辑 policy、不修改打包或 release、不提升为 Stage 5。".into(),
            );
            ui.set_load_latest_text("加载最新运行".into());
            ui.set_load_policy_text("加载策略".into());
            ui.set_load_run_list_text("加载运行列表摘要".into());
            ui.set_toggle_language_text("English".into());
        }
    }
    ui.set_bridge_status(status_text(language, status).into());
}

fn latest_summary_from_bridge() -> DashboardSummary {
    match run_dashboard_command(DashboardCommand::Latest) {
        Ok(stdout) => parse_latest_summary(&stdout)
            .unwrap_or_else(|error| DashboardSummary::command_failed(error.summary())),
        Err(BridgeError::Failed { stdout, .. }) if !stdout.is_empty() => {
            parse_latest_summary(&stdout)
                .unwrap_or_else(|error| DashboardSummary::command_failed(error.summary()))
        }
        Err(error) => DashboardSummary::command_failed(error.summary()),
    }
}

fn run_list_summary_from_bridge() -> DashboardSummary {
    match run_dashboard_command(DashboardCommand::List) {
        Ok(stdout) => parse_run_list_summary(&stdout)
            .unwrap_or_else(|error| DashboardSummary::command_failed(error.summary())),
        Err(BridgeError::Failed { stdout, .. }) if !stdout.is_empty() => {
            parse_run_list_summary(&stdout)
                .unwrap_or_else(|error| DashboardSummary::command_failed(error.summary()))
        }
        Err(error) => DashboardSummary::command_failed(error.summary()),
    }
}

fn policy_summary_from_bridge() -> DashboardSummary {
    match run_dashboard_command(DashboardCommand::Policy) {
        Ok(stdout) => parse_policy_summary(&stdout)
            .unwrap_or_else(|error| DashboardSummary::command_failed(error.summary())),
        Err(BridgeError::Failed { stdout, .. }) if !stdout.is_empty() => {
            parse_policy_summary(&stdout)
                .unwrap_or_else(|error| DashboardSummary::command_failed(error.summary()))
        }
        Err(error) => DashboardSummary::command_failed(error.summary()),
    }
}

fn main() -> Result<(), slint::PlatformError> {
    let ui = AppWindow::new()?;

    let mock_summary = DashboardSummary::mock();
    let current_language = Rc::new(Cell::new(Language::English));
    let bridge_status = Rc::new(Cell::new(mock_summary.bridge_status));

    apply_summary(&ui, &mock_summary, Language::English);
    apply_language(&ui, Language::English, mock_summary.bridge_status);

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();

    ui.on_toggle_language(move || {
        if let Some(ui) = ui_weak.upgrade() {
            let next_language = match callback_language.get() {
                Language::English => Language::Chinese,
                Language::Chinese => Language::English,
            };
            callback_language.set(next_language);
            apply_language(&ui, next_language, callback_status.get());
        }
    });

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();
    ui.on_load_latest(move || {
        if let Some(ui) = ui_weak.upgrade() {
            // Spike-only synchronous load: enough for fixed read-only commands, easy to make async later.
            let summary = latest_summary_from_bridge();
            callback_status.set(summary.bridge_status);
            apply_summary(&ui, &summary, callback_language.get());
        }
    });

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();
    ui.on_load_run_list(move || {
        if let Some(ui) = ui_weak.upgrade() {
            let summary = run_list_summary_from_bridge();
            callback_status.set(summary.bridge_status);
            apply_summary(&ui, &summary, callback_language.get());
        }
    });

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();
    ui.on_load_policy(move || {
        if let Some(ui) = ui_weak.upgrade() {
            let summary = policy_summary_from_bridge();
            callback_status.set(summary.bridge_status);
            apply_policy_summary(&ui, &summary, callback_language.get());
        }
    });

    ui.run()
}
