use serde_json::{json, Value};
use std::env;
use std::ffi::OsString;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const SCHEMA_VERSION: &str = "guard.event.v1";
const HEALTH_EVENT_TYPE: &str = "guard.health";
const PROCESS_SPAWN_EVENT_TYPE: &str = "process.spawn";
const GUARD_NAME: &str = "traceseal-guard";

#[derive(Debug, PartialEq)]
struct HealthConfig {
    out: PathBuf,
    workspace: PathBuf,
    pretty: bool,
}

#[derive(Debug, PartialEq)]
struct ProcessSpawnConfig {
    out: PathBuf,
    workspace: PathBuf,
    program: String,
    args: Vec<String>,
    cwd: Option<PathBuf>,
    pretty: bool,
}

#[derive(Debug, PartialEq)]
enum CommandConfig {
    Health(HealthConfig),
    ProcessSpawn(ProcessSpawnConfig),
}

fn usage() -> &'static str {
    "Usage:\n  traceseal-guard health --out <jsonl-path> --workspace <path> [--pretty]\n  traceseal-guard process-spawn --out <jsonl-path> --workspace <path> --program <program> [--arg <value> ...] [--cwd <path>] [--pretty]"
}

fn next_path<I>(args: &mut I, flag: &str) -> Result<PathBuf, String>
where
    I: Iterator<Item = OsString>,
{
    args.next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("{flag} requires a path"))
}

fn next_string<I>(args: &mut I, flag: &str) -> Result<String, String>
where
    I: Iterator<Item = OsString>,
{
    let value = args
        .next()
        .ok_or_else(|| format!("{flag} requires a value"))?;
    let value = value
        .into_string()
        .map_err(|_| format!("{flag} must be valid UTF-8"))?;
    if value.is_empty() {
        return Err(format!("{flag} requires a non-empty value"));
    }
    Ok(value)
}

fn parse_health_args<I>(mut args: I) -> Result<CommandConfig, String>
where
    I: Iterator<Item = OsString>,
{
    let mut out = None;
    let mut workspace = None;
    let mut pretty = false;

    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--out") => {
                if out.is_some() {
                    return Err("--out may only be specified once".to_string());
                }
                out = Some(next_path(&mut args, "--out")?);
            }
            Some("--workspace") => {
                if workspace.is_some() {
                    return Err("--workspace may only be specified once".to_string());
                }
                workspace = Some(next_path(&mut args, "--workspace")?);
            }
            Some("--pretty") => pretty = true,
            _ => return Err(format!("unknown argument '{}'", arg.to_string_lossy())),
        }
    }

    Ok(CommandConfig::Health(HealthConfig {
        out: out.ok_or_else(|| "missing required --out <jsonl-path>".to_string())?,
        workspace: workspace.ok_or_else(|| "missing required --workspace <path>".to_string())?,
        pretty,
    }))
}

fn parse_process_spawn_args<I>(mut args: I) -> Result<CommandConfig, String>
where
    I: Iterator<Item = OsString>,
{
    let mut out = None;
    let mut workspace = None;
    let mut program = None;
    let mut command_args = Vec::new();
    let mut cwd = None;
    let mut pretty = false;

    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--out") => {
                if out.is_some() {
                    return Err("--out may only be specified once".to_string());
                }
                out = Some(next_path(&mut args, "--out")?);
            }
            Some("--workspace") => {
                if workspace.is_some() {
                    return Err("--workspace may only be specified once".to_string());
                }
                workspace = Some(next_path(&mut args, "--workspace")?);
            }
            Some("--program") => {
                if program.is_some() {
                    return Err("--program may only be specified once".to_string());
                }
                program = Some(next_string(&mut args, "--program")?);
            }
            Some("--arg") => command_args.push(next_string(&mut args, "--arg")?),
            Some("--cwd") => {
                if cwd.is_some() {
                    return Err("--cwd may only be specified once".to_string());
                }
                cwd = Some(next_path(&mut args, "--cwd")?);
            }
            Some("--pretty") => pretty = true,
            _ => return Err(format!("unknown argument '{}'", arg.to_string_lossy())),
        }
    }

    Ok(CommandConfig::ProcessSpawn(ProcessSpawnConfig {
        out: out.ok_or_else(|| "missing required --out <jsonl-path>".to_string())?,
        workspace: workspace.ok_or_else(|| "missing required --workspace <path>".to_string())?,
        program: program.ok_or_else(|| "missing required --program <program>".to_string())?,
        args: command_args,
        cwd,
        pretty,
    }))
}

fn parse_args<I>(mut args: I) -> Result<CommandConfig, String>
where
    I: Iterator<Item = OsString>,
{
    let command = args
        .next()
        .ok_or_else(|| "missing subcommand; expected 'health' or 'process-spawn'".to_string())?;
    match command.to_str() {
        Some("health") => parse_health_args(args),
        Some("process-spawn") => parse_process_spawn_args(args),
        _ => Err(format!(
            "unsupported subcommand '{}'; expected 'health' or 'process-spawn'",
            command.to_string_lossy()
        )),
    }
}

fn civil_from_days(days_since_epoch: i64) -> (i64, u32, u32) {
    // Howard Hinnant's civil calendar conversion, adapted for Unix epoch days.
    let z = days_since_epoch + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let day_of_era = z - era * 146_097;
    let year_of_era =
        (day_of_era - day_of_era / 1_460 + day_of_era / 36_524 - day_of_era / 146_096) / 365;
    let mut year = year_of_era + era * 400;
    let day_of_year = day_of_era - (365 * year_of_era + year_of_era / 4 - year_of_era / 100);
    let month_prime = (5 * day_of_year + 2) / 153;
    let day = day_of_year - (153 * month_prime + 2) / 5 + 1;
    let month = month_prime + if month_prime < 10 { 3 } else { -9 };
    if month <= 2 {
        year += 1;
    }
    (year, month as u32, day as u32)
}

fn format_rfc3339_utc(duration: Duration) -> String {
    let seconds = duration.as_secs();
    let days = (seconds / 86_400) as i64;
    let seconds_of_day = seconds % 86_400;
    let hour = seconds_of_day / 3_600;
    let minute = (seconds_of_day % 3_600) / 60;
    let second = seconds_of_day % 60;
    let micros = duration.subsec_nanos() / 1_000;
    let (year, month, day) = civil_from_days(days);
    format!("{year:04}-{month:02}-{day:02}T{hour:02}:{minute:02}:{second:02}.{micros:06}Z")
}

fn event_identity(now: SystemTime) -> Result<(Duration, String), String> {
    let duration = now
        .duration_since(UNIX_EPOCH)
        .map_err(|_| "system clock is before the Unix epoch".to_string())?;
    let event_id = format!("guard_evt_{:020}_{}", duration.as_nanos(), process::id());
    Ok((duration, event_id))
}

fn health_event(workspace: &Path, now: SystemTime) -> Result<Value, String> {
    let (duration, event_id) = event_identity(now)?;
    let pid = process::id();
    let cwd = env::current_dir()
        .map_err(|error| format!("cannot determine current directory: {error}"))?;
    let process_name = env::current_exe().ok().and_then(|path| {
        path.file_name()
            .map(|name| name.to_string_lossy().into_owned())
    });

    Ok(json!({
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "timestamp": format_rfc3339_utc(duration),
        "source": "rust_guard",
        "event_type": HEALTH_EVENT_TYPE,
        "run_id": null,
        "workspace": workspace.to_string_lossy(),
        "process": {
            "pid": pid,
            "parent_pid": null,
            "process_name": process_name,
            "command_line": null,
            "cwd": cwd.to_string_lossy()
        },
        "target": null,
        "risk_level": "info",
        "policy": {
            "decision": "observe",
            "rule_id": null,
            "reason": "guard health event"
        },
        "redaction": {
            "status": "not_applicable",
            "fields": []
        },
        "guard": {
            "name": GUARD_NAME,
            "guard_version": env!("CARGO_PKG_VERSION"),
            "mode": "observe",
            "platform": env::consts::OS,
            "status": "ok"
        },
        "metadata": {
            "message": "guard health check ok"
        }
    }))
}

fn is_sensitive_key(value: &str) -> bool {
    let normalized = value
        .trim_start_matches('-')
        .trim_end_matches(':')
        .replace('-', "_")
        .to_ascii_lowercase();
    matches!(
        normalized.as_str(),
        "token"
            | "password"
            | "secret"
            | "authorization"
            | "cookie"
            | "api_key"
            | "apikey"
            | "access_token"
            | "client_secret"
    )
}

fn redact_command_line(program: &str, args: &[String]) -> (Vec<String>, Vec<String>) {
    let mut command_line = vec![program.to_string()];
    let mut fields = Vec::new();
    let mut redact_next = false;

    for arg in args {
        let index = command_line.len();
        if redact_next {
            command_line.push("<redacted>".to_string());
            fields.push(format!("process.command_line[{index}]"));
            redact_next = false;
            continue;
        }

        if let Some((key, _value)) = arg.split_once('=') {
            if is_sensitive_key(key) {
                command_line.push(format!("{key}=<redacted>"));
                fields.push(format!("process.command_line[{index}]"));
                continue;
            }
        }

        if is_sensitive_key(arg) {
            redact_next = true;
        }
        command_line.push(arg.clone());
    }

    (command_line, fields)
}

fn process_spawn_event(config: &ProcessSpawnConfig, now: SystemTime) -> Result<Value, String> {
    let (duration, event_id) = event_identity(now)?;
    let cwd = match &config.cwd {
        Some(path) => path.clone(),
        None => env::current_dir()
            .map_err(|error| format!("cannot determine current directory: {error}"))?,
    };
    let (command_line, redacted_fields) = redact_command_line(&config.program, &config.args);
    let redaction_status = if redacted_fields.is_empty() {
        "not_applicable"
    } else {
        "redacted"
    };

    Ok(json!({
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "timestamp": format_rfc3339_utc(duration),
        "source": "rust_guard",
        "event_type": PROCESS_SPAWN_EVENT_TYPE,
        "run_id": null,
        "workspace": config.workspace.to_string_lossy(),
        "process": {
            "pid": null,
            "parent_pid": null,
            "process_name": config.program,
            "command_line": command_line,
            "cwd": cwd.to_string_lossy()
        },
        "target": null,
        "risk_level": "info",
        "policy": {
            "decision": "observe",
            "rule_id": null,
            "reason": "process spawn dry-run event"
        },
        "redaction": {
            "status": redaction_status,
            "fields": redacted_fields
        },
        "guard": {
            "name": GUARD_NAME,
            "guard_version": env!("CARGO_PKG_VERSION"),
            "mode": "observe",
            "platform": env::consts::OS,
            "status": "ok"
        },
        "metadata": {
            "message": "process.spawn dry-run event emitted",
            "dry_run": true,
            "executed": false
        }
    }))
}

fn append_jsonl(path: &Path, event: &Value) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent).map_err(|error| {
                format!(
                    "cannot create output directory '{}': {error}",
                    parent.display()
                )
            })?;
        }
    }

    let line = serde_json::to_string(event)
        .map_err(|error| format!("cannot serialize Guard event: {error}"))?;
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|error| format!("cannot open output '{}': {error}", path.display()))?;
    file.write_all(line.as_bytes())
        .and_then(|_| file.write_all(b"\n"))
        .and_then(|_| file.flush())
        .map_err(|error| format!("cannot write output '{}': {error}", path.display()))
}

fn emit(out: &Path, event: &Value, pretty: bool) -> Result<(), String> {
    append_jsonl(out, event)?;
    let stdout = if pretty {
        serde_json::to_string_pretty(event)
    } else {
        serde_json::to_string(event)
    }
    .map_err(|error| format!("cannot serialize stdout event: {error}"))?;
    println!("{stdout}");
    Ok(())
}

fn run() -> Result<(), String> {
    match parse_args(env::args_os().skip(1))? {
        CommandConfig::Health(config) => {
            let event = health_event(&config.workspace, SystemTime::now())?;
            emit(&config.out, &event, config.pretty)
        }
        CommandConfig::ProcessSpawn(config) => {
            let event = process_spawn_event(&config, SystemTime::now())?;
            emit(&config.out, &event, config.pretty)
        }
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("traceseal-guard: {error}\n\n{}", usage());
        process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parse(values: &[&str]) -> Result<CommandConfig, String> {
        parse_args(values.iter().map(OsString::from))
    }

    #[test]
    fn parses_health_arguments() {
        let config = parse(&[
            "health",
            "--out",
            "tmp/health.jsonl",
            "--workspace",
            ".",
            "--pretty",
        ])
        .expect("valid arguments");
        assert_eq!(
            config,
            CommandConfig::Health(HealthConfig {
                out: PathBuf::from("tmp/health.jsonl"),
                workspace: PathBuf::from("."),
                pretty: true,
            })
        );
    }

    #[test]
    fn parses_process_spawn_arguments() {
        let config = parse(&[
            "process-spawn",
            "--out",
            "tmp/spawn.jsonl",
            "--workspace",
            ".",
            "--program",
            "python",
            "--arg",
            "example.py",
            "--arg",
            "safe=value",
            "--cwd",
            "workspace",
        ])
        .expect("valid arguments");
        assert_eq!(
            config,
            CommandConfig::ProcessSpawn(ProcessSpawnConfig {
                out: PathBuf::from("tmp/spawn.jsonl"),
                workspace: PathBuf::from("."),
                program: "python".to_string(),
                args: vec!["example.py".to_string(), "safe=value".to_string()],
                cwd: Some(PathBuf::from("workspace")),
                pretty: false,
            })
        );
    }

    #[test]
    fn rejects_missing_arguments_without_panicking() {
        let health_error = parse(&["health"]).unwrap_err();
        assert!(health_error.contains("--out"));
        let spawn_error = parse(&[
            "process-spawn",
            "--out",
            "tmp/spawn.jsonl",
            "--workspace",
            ".",
        ])
        .unwrap_err();
        assert!(spawn_error.contains("--program"));
    }

    #[test]
    fn formats_rfc3339_utc() {
        assert_eq!(
            format_rfc3339_utc(Duration::from_secs(0)),
            "1970-01-01T00:00:00.000000Z"
        );
        assert_eq!(
            format_rfc3339_utc(Duration::new(86_400, 123_456_000)),
            "1970-01-02T00:00:00.123456Z"
        );
    }

    #[test]
    fn health_event_matches_v1_contract() {
        let event = health_event(Path::new("workspace"), UNIX_EPOCH + Duration::from_secs(1))
            .expect("health event");
        assert_eq!(event["schema_version"], SCHEMA_VERSION);
        assert_eq!(event["event_type"], HEALTH_EVENT_TYPE);
        assert_eq!(event["risk_level"], "info");
        assert_eq!(event["policy"]["decision"], "observe");
        assert_eq!(event["redaction"]["status"], "not_applicable");
        assert_eq!(event["guard"]["name"], GUARD_NAME);
        assert_eq!(event["guard"]["mode"], "observe");
        assert_eq!(event["guard"]["status"], "ok");
        assert_eq!(event["metadata"]["message"], "guard health check ok");
        assert!(event["process"]["pid"].is_number());
    }

    fn spawn_config(args: Vec<String>) -> ProcessSpawnConfig {
        ProcessSpawnConfig {
            out: PathBuf::from("unused.jsonl"),
            workspace: PathBuf::from("workspace"),
            program: "python".to_string(),
            args,
            cwd: Some(PathBuf::from("workspace")),
            pretty: false,
        }
    }

    #[test]
    fn process_spawn_event_matches_v1_dry_run_contract() {
        let event = process_spawn_event(
            &spawn_config(vec!["example.py".to_string()]),
            UNIX_EPOCH + Duration::from_secs(1),
        )
        .expect("process.spawn event");
        assert_eq!(event["schema_version"], SCHEMA_VERSION);
        assert_eq!(event["event_type"], PROCESS_SPAWN_EVENT_TYPE);
        assert_eq!(event["process"]["process_name"], "python");
        assert_eq!(event["process"]["command_line"][0], "python");
        assert_eq!(event["process"]["command_line"][1], "example.py");
        assert!(event["process"]["pid"].is_null());
        assert_eq!(event["policy"]["decision"], "observe");
        assert_eq!(event["guard"]["mode"], "observe");
        assert_eq!(event["metadata"]["dry_run"], true);
        assert_eq!(event["metadata"]["executed"], false);
    }

    #[test]
    fn redacts_sensitive_process_arguments_before_serialization() {
        let event = process_spawn_event(
            &spawn_config(vec![
                "--token".to_string(),
                "secret-value".to_string(),
                "password=hunter2".to_string(),
                "safe=value".to_string(),
            ]),
            UNIX_EPOCH + Duration::from_secs(1),
        )
        .expect("process.spawn event");
        let serialized = serde_json::to_string(&event).expect("serialize");
        assert!(!serialized.contains("secret-value"));
        assert!(!serialized.contains("hunter2"));
        assert!(serialized.contains("<redacted>"));
        assert_eq!(event["redaction"]["status"], "redacted");
        assert_eq!(
            event["redaction"]["fields"]
                .as_array()
                .expect("fields")
                .len(),
            2
        );
    }

    #[test]
    fn process_spawn_event_does_not_execute_target() {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let marker = env::temp_dir().join(format!(
            "traceseal_guard_must_not_exist_{}_{}",
            process::id(),
            unique
        ));
        let config = ProcessSpawnConfig {
            program: "target-that-must-not-run".to_string(),
            args: vec![marker.to_string_lossy().into_owned()],
            ..spawn_config(Vec::new())
        };
        let event = process_spawn_event(&config, SystemTime::now()).expect("dry-run event");
        assert_eq!(event["metadata"]["executed"], false);
        assert!(!marker.exists());
    }

    #[test]
    fn appends_one_json_object_per_line() {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root =
            env::temp_dir().join(format!("traceseal_guard_test_{}_{}", process::id(), unique));
        let path = root.join("nested").join("events.jsonl");
        let health = health_event(Path::new("workspace"), UNIX_EPOCH + Duration::from_secs(1))
            .expect("health event");
        let spawn = process_spawn_event(
            &spawn_config(vec!["example.py".to_string()]),
            UNIX_EPOCH + Duration::from_secs(2),
        )
        .expect("process.spawn event");
        append_jsonl(&path, &health).expect("first append");
        append_jsonl(&path, &spawn).expect("second append");
        let contents = fs::read_to_string(&path).expect("read fixture");
        let lines: Vec<_> = contents.lines().collect();
        assert_eq!(lines.len(), 2);
        assert_eq!(
            serde_json::from_str::<Value>(lines[0]).expect("health JSON")["event_type"],
            HEALTH_EVENT_TYPE
        );
        assert_eq!(
            serde_json::from_str::<Value>(lines[1]).expect("spawn JSON")["event_type"],
            PROCESS_SPAWN_EVENT_TYPE
        );
        let _ = fs::remove_dir_all(root);
    }
}
