use std::process::Command;

const PYTHON_EXECUTABLE: &str = "python";
const MAX_DIAGNOSTIC_LEN: usize = 240;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DashboardCommand {
    Latest,
    List,
    Policy,
}

impl DashboardCommand {
    pub fn args(self) -> &'static [&'static str] {
        match self {
            DashboardCommand::Latest => &["-m", "traceseal", "dashboard-data", "latest"],
            DashboardCommand::List => &["-m", "traceseal", "dashboard-data", "list"],
            DashboardCommand::Policy => &["-m", "traceseal", "dashboard-data", "policy"],
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BridgeError {
    Io(String),
    Failed {
        status: Option<i32>,
        stderr: String,
        stdout: String,
    },
    InvalidUtf8(String),
}

impl BridgeError {
    pub fn summary(&self) -> String {
        match self {
            BridgeError::Io(message) => {
                format!("dashboard-data command could not start: {message}")
            }
            BridgeError::Failed { status, stderr, .. } => {
                let status_text = status
                    .map(|code| code.to_string())
                    .unwrap_or_else(|| "unknown".to_string());
                if stderr.is_empty() {
                    format!("dashboard-data command failed with exit code {status_text}")
                } else {
                    format!("dashboard-data command failed with exit code {status_text}: {stderr}")
                }
            }
            BridgeError::InvalidUtf8(message) => {
                format!("dashboard-data command returned invalid UTF-8: {message}")
            }
        }
    }
}

pub fn command_args(command: DashboardCommand) -> &'static [&'static str] {
    command.args()
}

pub fn python_executable() -> &'static str {
    PYTHON_EXECUTABLE
}

pub fn run_dashboard_command(command: DashboardCommand) -> Result<String, BridgeError> {
    let output = Command::new(python_executable())
        .args(command_args(command))
        .output()
        .map_err(|error| BridgeError::Io(sanitize_diagnostic(&error.to_string())))?;

    if !output.status.success() {
        return Err(BridgeError::Failed {
            status: output.status.code(),
            stderr: sanitize_diagnostic(&String::from_utf8_lossy(&output.stderr)),
            stdout: sanitize_diagnostic(&String::from_utf8_lossy(&output.stdout)),
        });
    }

    String::from_utf8(output.stdout)
        .map_err(|error| BridgeError::InvalidUtf8(sanitize_diagnostic(&error.to_string())))
}

fn sanitize_diagnostic(message: &str) -> String {
    let collapsed = message.split_whitespace().collect::<Vec<_>>().join(" ");
    collapsed.chars().take(MAX_DIAGNOSTIC_LEN).collect()
}

#[cfg(test)]
mod tests {
    use super::{command_args, DashboardCommand};

    #[test]
    fn latest_command_args_are_fixed() {
        assert_eq!(
            command_args(DashboardCommand::Latest),
            &["-m", "traceseal", "dashboard-data", "latest"]
        );
    }

    #[test]
    fn list_command_args_are_fixed() {
        assert_eq!(
            command_args(DashboardCommand::List),
            &["-m", "traceseal", "dashboard-data", "list"]
        );
    }

    #[test]
    fn policy_command_args_are_fixed() {
        assert_eq!(
            command_args(DashboardCommand::Policy),
            &["-m", "traceseal", "dashboard-data", "policy"]
        );
    }

    #[test]
    fn fixed_commands_do_not_include_run_or_shell_metacharacters() {
        let shell_metacharacters = [";", "&", "|", ">", "<", "`", "$(", "&&", "||"];
        for command in [
            DashboardCommand::Latest,
            DashboardCommand::List,
            DashboardCommand::Policy,
        ] {
            let args = command_args(command);
            assert!(!args.iter().any(|arg| *arg == "run"));
            assert!(args
                .iter()
                .all(|arg| !shell_metacharacters.iter().any(|token| arg.contains(token))));
        }
    }
}
