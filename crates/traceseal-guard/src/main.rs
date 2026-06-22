use serde_json::{json, Value};
use std::env;
use std::ffi::OsString;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const SCHEMA_VERSION: &str = "guard.event.v1";
const EVENT_TYPE: &str = "guard.health";
const GUARD_NAME: &str = "traceseal-guard";

#[derive(Debug, PartialEq)]
struct Config {
    out: PathBuf,
    workspace: PathBuf,
    pretty: bool,
}

fn usage() -> &'static str {
    "Usage: traceseal-guard health --out <jsonl-path> --workspace <path> [--pretty]"
}

fn parse_args<I>(mut args: I) -> Result<Config, String>
where
    I: Iterator<Item = OsString>,
{
    let command = args
        .next()
        .ok_or_else(|| "missing subcommand; expected 'health'".to_string())?;
    if command != "health" {
        return Err(format!(
            "unsupported subcommand '{}'; expected 'health'",
            command.to_string_lossy()
        ));
    }

    let mut out = None;
    let mut workspace = None;
    let mut pretty = false;

    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--out") => {
                if out.is_some() {
                    return Err("--out may only be specified once".to_string());
                }
                out = Some(
                    args.next()
                        .ok_or_else(|| "--out requires a JSONL path".to_string())?
                        .into(),
                );
            }
            Some("--workspace") => {
                if workspace.is_some() {
                    return Err("--workspace may only be specified once".to_string());
                }
                workspace = Some(
                    args.next()
                        .ok_or_else(|| "--workspace requires a path".to_string())?
                        .into(),
                );
            }
            Some("--pretty") => pretty = true,
            _ => return Err(format!("unknown argument '{}'", arg.to_string_lossy())),
        }
    }

    Ok(Config {
        out: out.ok_or_else(|| "missing required --out <jsonl-path>".to_string())?,
        workspace: workspace.ok_or_else(|| "missing required --workspace <path>".to_string())?,
        pretty,
    })
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

fn health_event(workspace: &Path, now: SystemTime) -> Result<Value, String> {
    let duration = now
        .duration_since(UNIX_EPOCH)
        .map_err(|_| "system clock is before the Unix epoch".to_string())?;
    let pid = process::id();
    let event_id = format!("guard_evt_{:020}_{pid}", duration.as_nanos());
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
        "event_type": EVENT_TYPE,
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
        .map_err(|error| format!("cannot serialize guard.health event: {error}"))?;
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

fn run() -> Result<(), String> {
    let config = parse_args(env::args_os().skip(1))?;
    let event = health_event(&config.workspace, SystemTime::now())?;
    append_jsonl(&config.out, &event)?;

    let stdout = if config.pretty {
        serde_json::to_string_pretty(&event)
    } else {
        serde_json::to_string(&event)
    }
    .map_err(|error| format!("cannot serialize stdout event: {error}"))?;
    println!("{stdout}");
    Ok(())
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

    #[test]
    fn parses_health_arguments() {
        let config = parse_args(
            [
                "health",
                "--out",
                "tmp/health.jsonl",
                "--workspace",
                ".",
                "--pretty",
            ]
            .into_iter()
            .map(OsString::from),
        )
        .expect("valid arguments");
        assert_eq!(config.out, PathBuf::from("tmp/health.jsonl"));
        assert_eq!(config.workspace, PathBuf::from("."));
        assert!(config.pretty);
    }

    #[test]
    fn rejects_missing_arguments_without_panicking() {
        let error = parse_args([OsString::from("health")].into_iter()).unwrap_err();
        assert!(error.contains("--out"));
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
        assert_eq!(event["event_type"], EVENT_TYPE);
        assert_eq!(event["risk_level"], "info");
        assert_eq!(event["policy"]["decision"], "observe");
        assert_eq!(event["redaction"]["status"], "not_applicable");
        assert_eq!(event["guard"]["name"], GUARD_NAME);
        assert_eq!(event["guard"]["mode"], "observe");
        assert_eq!(event["guard"]["status"], "ok");
        assert_eq!(event["metadata"]["message"], "guard health check ok");
        assert!(event["process"]["pid"].is_number());
    }

    #[test]
    fn appends_one_json_object_per_line() {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let path = env::temp_dir()
            .join(format!("traceseal_guard_test_{}_{}", process::id(), unique))
            .join("nested")
            .join("health.jsonl");
        let event = health_event(Path::new("workspace"), UNIX_EPOCH + Duration::from_secs(1))
            .expect("health event");
        append_jsonl(&path, &event).expect("first append");
        append_jsonl(&path, &event).expect("second append");
        let contents = fs::read_to_string(&path).expect("read fixture");
        let lines: Vec<_> = contents.lines().collect();
        assert_eq!(lines.len(), 2);
        for line in lines {
            let parsed: Value = serde_json::from_str(line).expect("valid JSONL record");
            assert_eq!(parsed["event_type"], EVENT_TYPE);
        }
        if let Some(root) = path.ancestors().nth(2) {
            let _ = fs::remove_dir_all(root);
        }
    }
}
