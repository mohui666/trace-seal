export type RiskLevel = "low" | "medium" | "high" | "critical";
export type PolicyAction = "allow" | "warn" | "deny" | "block" | "require_approval";
export type RunStatus = "completed" | "failed" | "blocked" | "running";
export type EventType = "file.write" | "file.delete" | "shell" | "http" | "sdk" | string;

export interface FileChange {
  path: string;
  change_type: "created" | "modified" | "deleted" | string;
  before_sha256?: string;
  after_sha256?: string;
}

export interface TraceEvent {
  id: string;
  seq?: number;
  ts?: string;
  type: EventType;
  operation?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  risk?: {
    level?: RiskLevel;
    reasons?: string[];
    policy_rule?: string;
    action?: PolicyAction;
    suggested_policy?: string;
  };
  file_changes?: FileChange[];
}

export interface DashboardRunExport {
  schema_version: number;
  run_id: string;
  command: string;
  started_at?: string;
  finished_at?: string;
  status?: RunStatus;
  exit_code?: number;
  event_count: number;
  high_risk_count: number;
  first_harmful_event?: TraceEvent | null;
  events: TraceEvent[];
  affected_files: string[];
  suggested_policy?: string | null;
}

export interface RunSummary {
  run_id: string;
  command: string;
  started_at?: string;
  finished_at?: string;
  status?: RunStatus;
  exit_code?: number;
  event_count: number;
  high_risk_count: number;
  first_harmful_event_id?: string | null;
}

export interface PolicyRule {
  rule_id: string;
  event_type?: string;
  pattern?: string;
  risk_level?: RiskLevel;
  action?: PolicyAction;
  description?: string;
  suggested_policy?: string;
}

export interface RuntimeInfo {
  pythonCommand: string;
  repositoryRoot: string;
  platform: string;
  version?: string;
}

export interface WorkspaceInfo {
  path: string | null;
  valid: boolean;
  hasRuns: boolean;
  hasPolicy: boolean;
}

export interface TraceSealApi {
  getLatestRun(): Promise<DashboardRunExport>;
  listRuns(): Promise<RunSummary[]>;
  getRun(runId: string): Promise<DashboardRunExport>;
  getPolicy(): Promise<PolicyRule[]>;
  getRuntimeInfo(): Promise<RuntimeInfo>;
  selectWorkspace(): Promise<WorkspaceInfo>;
  getWorkspace(): Promise<WorkspaceInfo>;
  clearWorkspace(): Promise<void>;
}

export type TraceSealErrorCode =
  | "PYTHON_NOT_FOUND"
  | "COMMAND_FAILED"
  | "INVALID_JSON"
  | "RUN_NOT_FOUND"
  | "INVALID_RUN_ID"
  | "INVALID_WORKSPACE"
  | "TIMEOUT"
  | "INTERNAL_ERROR";

export class TraceSealRuntimeError extends Error {
  public readonly code: TraceSealErrorCode;
  public readonly details?: unknown;

  constructor(code: TraceSealErrorCode, message: string, details?: unknown) {
    super(message);
    this.name = "TraceSealRuntimeError";
    this.code = code;
    this.details = details;
  }
}
