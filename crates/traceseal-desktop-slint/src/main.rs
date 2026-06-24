use std::{
    sync::{
        atomic::{AtomicU64, AtomicU8, Ordering},
        Arc,
    },
    thread,
};

mod dashboard_data;
mod summary;

use dashboard_data::{
    read_demo_fixture_bundle, run_dashboard_command, BridgeError, DashboardCommand,
};
use summary::{
    parse_demo_fixture_summary, parse_latest_summary, parse_policy_summary, parse_run_list_summary,
    BridgeStatusKind, DashboardLoadState, DashboardSummary,
};

slint::include_modules!();

#[derive(Clone, Copy, PartialEq, Eq)]
enum Language {
    English,
    Chinese,
}

#[derive(Clone, Copy)]
enum DashboardLoadKind {
    Latest,
    RunList,
    Policy,
    DemoFixture,
}

fn language_index(language: Language) -> u8 {
    match language {
        Language::English => 0,
        Language::Chinese => 1,
    }
}

fn language_from_index(index: u8) -> Language {
    match index {
        1 => Language::Chinese,
        _ => Language::English,
    }
}

fn status_index(status: BridgeStatusKind) -> u8 {
    match status {
        BridgeStatusKind::MockFallback => 0,
        BridgeStatusKind::Loaded => 1,
        BridgeStatusKind::CommandFailed => 2,
        BridgeStatusKind::NoRunsFound => 3,
        BridgeStatusKind::DemoFixture => 4,
    }
}

fn status_from_index(index: u8) -> BridgeStatusKind {
    match index {
        1 => BridgeStatusKind::Loaded,
        2 => BridgeStatusKind::CommandFailed,
        3 => BridgeStatusKind::NoRunsFound,
        4 => BridgeStatusKind::DemoFixture,
        _ => BridgeStatusKind::MockFallback,
    }
}

fn status_text(language: Language, status: BridgeStatusKind) -> &'static str {
    match (language, status) {
        (Language::English, BridgeStatusKind::MockFallback) => "mock fallback",
        (Language::English, BridgeStatusKind::Loaded) => "loaded from dashboard-data",
        (Language::English, BridgeStatusKind::CommandFailed) => "command failed",
        (Language::English, BridgeStatusKind::NoRunsFound) => "no runs found",
        (Language::English, BridgeStatusKind::DemoFixture) => "showing demo fixture data",
        (Language::Chinese, BridgeStatusKind::MockFallback) => "mock 兜底",
        (Language::Chinese, BridgeStatusKind::Loaded) => "已从 dashboard-data 加载",
        (Language::Chinese, BridgeStatusKind::CommandFailed) => "命令失败",
        (Language::Chinese, BridgeStatusKind::NoRunsFound) => "未找到运行记录",
        (Language::Chinese, BridgeStatusKind::DemoFixture) => "当前显示示例数据",
    }
}

fn loading_message(language: Language, kind: DashboardLoadKind) -> &'static str {
    match (language, kind) {
        (Language::English, DashboardLoadKind::DemoFixture) => "Loading demo fixture data...",
        (Language::English, _) => "Loading dashboard data...",
        (Language::Chinese, DashboardLoadKind::DemoFixture) => "正在加载示例数据...",
        (Language::Chinese, _) => "正在加载 dashboard 数据...",
    }
}

fn loaded_message(language: Language, status: BridgeStatusKind) -> &'static str {
    match (language, status) {
        (Language::English, BridgeStatusKind::DemoFixture) => "Demo fixture data loaded",
        (Language::English, _) => "Dashboard data loaded",
        (Language::Chinese, BridgeStatusKind::DemoFixture) => "示例数据已加载",
        (Language::Chinese, _) => "dashboard 数据已加载",
    }
}

fn failed_message(language: Language) -> &'static str {
    match language {
        Language::English => "Failed to load dashboard data",
        Language::Chinese => "dashboard 数据加载失败",
    }
}

fn error_message(language: Language, detail: &str) -> String {
    if detail.is_empty() || detail == "none" {
        failed_message(language).to_string()
    } else {
        format!("{}: {detail}", failed_message(language))
    }
}

fn apply_summary(ui: &AppWindow, summary: &DashboardSummary, language: Language) {
    ui.set_is_demo_data(summary.bridge_status == BridgeStatusKind::DemoFixture);
    ui.set_data_source(summary.data_source.clone().into());
    ui.set_latest_run(summary.latest_run_id.clone().into());
    ui.set_latest_status(summary.latest_status.clone().into());
    ui.set_event_count(summary.event_count);
    ui.set_risk_count(summary.risk_count);
    ui.set_policy_mode(summary.policy_summary.clone().into());
    ui.set_started_at(summary.started_at.clone().into());
    ui.set_finished_at(summary.finished_at.clone().into());
    ui.set_run_title(summary.run_title.clone().into());
    ui.set_workspace(summary.workspace.clone().into());
    ui.set_run_policy_mode(summary.run_policy_mode.clone().into());
    ui.set_risk_summary(summary.risk_summary.clone().into());
    ui.set_bridge_status(status_text(language, summary.bridge_status).into());
    ui.set_last_error(summary.last_error.clone().into());
}

fn apply_policy_summary(ui: &AppWindow, summary: &DashboardSummary, language: Language) {
    if summary.bridge_status == BridgeStatusKind::DemoFixture {
        ui.set_is_demo_data(true);
    }
    ui.set_data_source(summary.data_source.clone().into());
    ui.set_policy_mode(summary.policy_summary.clone().into());
    ui.set_bridge_status(status_text(language, summary.bridge_status).into());
    ui.set_last_error(summary.last_error.clone().into());
}

fn apply_load_state(
    ui: &AppWindow,
    state: &DashboardLoadState,
    language: Language,
    status: BridgeStatusKind,
) {
    ui.set_is_loading(state.is_loading);
    ui.set_has_error(state.has_error);
    ui.set_has_data(state.has_data);
    ui.set_loading_message(state.loading_message.clone().into());
    ui.set_error_message(state.error_message.clone().into());
    ui.set_status_message(state.status_message.clone().into());

    if state.is_loading {
        ui.set_bridge_status(state.status_message.clone().into());
    } else {
        ui.set_bridge_status(status_text(language, status).into());
    }
}

fn apply_localized_load_state(ui: &AppWindow, language: Language, status: BridgeStatusKind) {
    if ui.get_is_loading() {
        apply_load_state(
            ui,
            &DashboardLoadState::loading(loading_message(language, DashboardLoadKind::Latest)),
            language,
            status,
        );
    } else if ui.get_has_error() {
        let detail = ui.get_last_error().to_string();
        apply_load_state(
            ui,
            &DashboardLoadState::error(error_message(language, &detail)),
            language,
            BridgeStatusKind::CommandFailed,
        );
    } else if ui.get_has_data() {
        apply_load_state(
            ui,
            &DashboardLoadState::loaded(loaded_message(language, status)),
            language,
            status,
        );
    }
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
            ui.set_run_detail_title("Run detail".into());
            ui.set_detail_run_id_label("Run ID".into());
            ui.set_started_at_label("Started".into());
            ui.set_finished_at_label("Finished".into());
            ui.set_run_title_label("Title".into());
            ui.set_workspace_label("Workspace".into());
            ui.set_run_policy_mode_label("Policy mode".into());
            ui.set_risk_summary_label("Risk summary".into());
            ui.set_last_error_label("Last error".into());
            ui.set_boundary_text(
                "Read-only spike: Electron remains default. Uses only fixed Python Core dashboard-data commands. No traceseal run, target commands, workspace writes, policy edits, packaging changes, release changes, or Stage 5 promotion.".into(),
            );
            ui.set_load_latest_text("Refresh".into());
            ui.set_load_policy_text("Load policy".into());
            ui.set_load_run_list_text("Load run list summary".into());
            ui.set_load_demo_text("Load demo data".into());
            ui.set_demo_source_text("Showing demo fixture data".into());
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
            ui.set_run_detail_title("运行详情".into());
            ui.set_detail_run_id_label("运行 ID".into());
            ui.set_started_at_label("开始时间".into());
            ui.set_finished_at_label("结束时间".into());
            ui.set_run_title_label("标题".into());
            ui.set_workspace_label("工作区".into());
            ui.set_run_policy_mode_label("策略模式".into());
            ui.set_risk_summary_label("风险摘要".into());
            ui.set_last_error_label("最近错误".into());
            ui.set_boundary_text(
                "只读实验：Electron 仍是默认桌面实现。仅使用固定 Python Core dashboard-data 命令。不调用 traceseal run、不执行目标命令、不写入 workspace、不编辑 policy、不修改打包或 release、不提升为 Stage 5。".into(),
            );
            ui.set_load_latest_text("刷新".into());
            ui.set_load_policy_text("加载策略".into());
            ui.set_load_run_list_text("加载运行列表摘要".into());
            ui.set_load_demo_text("加载示例数据".into());
            ui.set_demo_source_text("当前显示示例数据".into());
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

fn demo_summary_from_fixtures() -> DashboardSummary {
    match read_demo_fixture_bundle() {
        Ok(bundle) => {
            parse_demo_fixture_summary(&bundle.latest_json, &bundle.list_json, &bundle.policy_json)
                .unwrap_or_else(|error| DashboardSummary::demo_fixture_failed(error.summary()))
        }
        Err(error) => DashboardSummary::demo_fixture_failed(error.summary()),
    }
}

fn summary_from_bridge(kind: DashboardLoadKind) -> DashboardSummary {
    match kind {
        DashboardLoadKind::Latest => latest_summary_from_bridge(),
        DashboardLoadKind::RunList => run_list_summary_from_bridge(),
        DashboardLoadKind::Policy => policy_summary_from_bridge(),
        DashboardLoadKind::DemoFixture => demo_summary_from_fixtures(),
    }
}

fn start_dashboard_load(
    ui_weak: slint::Weak<AppWindow>,
    kind: DashboardLoadKind,
    language: Arc<AtomicU8>,
    bridge_status: Arc<AtomicU8>,
    load_generation: Arc<AtomicU64>,
) {
    let load_id = load_generation.fetch_add(1, Ordering::AcqRel) + 1;
    let current_language = language_from_index(language.load(Ordering::Acquire));
    let current_status = status_from_index(bridge_status.load(Ordering::Acquire));

    if let Some(ui) = ui_weak.upgrade() {
        apply_load_state(
            &ui,
            &DashboardLoadState::loading(loading_message(current_language, kind)),
            current_language,
            current_status,
        );
    }

    thread::spawn(move || {
        let summary = summary_from_bridge(kind);
        let _ = slint::invoke_from_event_loop(move || {
            if load_generation.load(Ordering::Acquire) != load_id {
                return;
            }

            let Some(ui) = ui_weak.upgrade() else {
                return;
            };

            let current_language = language_from_index(language.load(Ordering::Acquire));
            let status = summary.bridge_status;
            bridge_status.store(status_index(status), Ordering::Release);

            match kind {
                DashboardLoadKind::Policy => apply_policy_summary(&ui, &summary, current_language),
                DashboardLoadKind::Latest
                | DashboardLoadKind::RunList
                | DashboardLoadKind::DemoFixture => apply_summary(&ui, &summary, current_language),
            }

            if status == BridgeStatusKind::CommandFailed {
                apply_load_state(
                    &ui,
                    &DashboardLoadState::error(error_message(
                        current_language,
                        &summary.last_error,
                    )),
                    current_language,
                    BridgeStatusKind::CommandFailed,
                );
            } else {
                apply_load_state(
                    &ui,
                    &DashboardLoadState::loaded(loaded_message(current_language, status)),
                    current_language,
                    status,
                );
            }
        });
    });
}

fn main() -> Result<(), slint::PlatformError> {
    let ui = AppWindow::new()?;

    let mock_summary = DashboardSummary::mock();
    let current_language = Arc::new(AtomicU8::new(language_index(Language::English)));
    let bridge_status = Arc::new(AtomicU8::new(status_index(mock_summary.bridge_status)));
    let load_generation = Arc::new(AtomicU64::new(0));

    apply_summary(&ui, &mock_summary, Language::English);
    apply_language(&ui, Language::English, mock_summary.bridge_status);
    apply_load_state(
        &ui,
        &DashboardLoadState::loading(loading_message(
            Language::English,
            DashboardLoadKind::Latest,
        )),
        Language::English,
        mock_summary.bridge_status,
    );

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();

    ui.on_toggle_language(move || {
        if let Some(ui) = ui_weak.upgrade() {
            let current_language = language_from_index(callback_language.load(Ordering::Acquire));
            let next_language = match current_language {
                Language::English => Language::Chinese,
                Language::Chinese => Language::English,
            };
            callback_language.store(language_index(next_language), Ordering::Release);
            let status = status_from_index(callback_status.load(Ordering::Acquire));
            apply_language(&ui, next_language, status);
            apply_localized_load_state(&ui, next_language, status);
        }
    });

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();
    let callback_generation = load_generation.clone();
    ui.on_load_latest(move || {
        start_dashboard_load(
            ui_weak.clone(),
            DashboardLoadKind::Latest,
            callback_language.clone(),
            callback_status.clone(),
            callback_generation.clone(),
        );
    });

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();
    let callback_generation = load_generation.clone();
    ui.on_load_run_list(move || {
        start_dashboard_load(
            ui_weak.clone(),
            DashboardLoadKind::RunList,
            callback_language.clone(),
            callback_status.clone(),
            callback_generation.clone(),
        );
    });

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();
    let callback_generation = load_generation.clone();
    ui.on_load_policy(move || {
        start_dashboard_load(
            ui_weak.clone(),
            DashboardLoadKind::Policy,
            callback_language.clone(),
            callback_status.clone(),
            callback_generation.clone(),
        );
    });

    let ui_weak = ui.as_weak();
    let callback_language = current_language.clone();
    let callback_status = bridge_status.clone();
    let callback_generation = load_generation.clone();
    ui.on_load_demo(move || {
        start_dashboard_load(
            ui_weak.clone(),
            DashboardLoadKind::DemoFixture,
            callback_language.clone(),
            callback_status.clone(),
            callback_generation.clone(),
        );
    });

    start_dashboard_load(
        ui.as_weak(),
        DashboardLoadKind::Latest,
        current_language,
        bridge_status,
        load_generation,
    );

    ui.run()
}
