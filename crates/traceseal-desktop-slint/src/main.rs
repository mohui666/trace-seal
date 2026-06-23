use std::{cell::Cell, rc::Rc};

slint::include_modules!();

#[derive(Clone, Copy)]
enum Language {
    English,
    Chinese,
}

fn apply_language(ui: &AppWindow, language: Language) {
    match language {
        Language::English => {
            ui.set_title_text("TraceSeal Slint Spike".into());
            ui.set_subtitle_text("Experimental only".into());
            ui.set_latest_run_label("Latest run".into());
            ui.set_event_count_label("Event count".into());
            ui.set_risk_count_label("Risk count".into());
            ui.set_policy_mode_label("Policy mode".into());
            ui.set_boundary_text(
                "Electron remains default. Python Core is not called. No real runs are loaded. No packaging or release changes.".into(),
            );
            ui.set_toggle_language_text("中文".into());
        }
        Language::Chinese => {
            ui.set_title_text("TraceSeal Slint 实验窗口".into());
            ui.set_subtitle_text("仅实验用途".into());
            ui.set_latest_run_label("最新运行".into());
            ui.set_event_count_label("事件数量".into());
            ui.set_risk_count_label("风险数量".into());
            ui.set_policy_mode_label("策略模式".into());
            ui.set_boundary_text(
                "Electron 仍是默认桌面实现。不会调用 Python Core。不会加载真实 runs 数据。不会修改打包或 release。".into(),
            );
            ui.set_toggle_language_text("English".into());
        }
    }
}

fn main() -> Result<(), slint::PlatformError> {
    let ui = AppWindow::new()?;

    ui.set_latest_run("mock-run-0001".into());
    ui.set_event_count(12);
    ui.set_risk_count(3);
    ui.set_policy_mode("mock / read-only".into());

    apply_language(&ui, Language::English);

    let ui_weak = ui.as_weak();
    let current_language = Rc::new(Cell::new(Language::English));
    let callback_language = current_language.clone();

    ui.on_toggle_language(move || {
        if let Some(ui) = ui_weak.upgrade() {
            let next_language = match callback_language.get() {
                Language::English => Language::Chinese,
                Language::Chinese => Language::English,
            };
            callback_language.set(next_language);
            apply_language(&ui, next_language);
        }
    });

    ui.run()
}
