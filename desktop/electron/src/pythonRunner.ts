import { spawn, SpawnOptionsWithoutStdio } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { bundledCoreExecutablePath } from "./runtimePaths";
import { DashboardRunExport, PolicyRule, RunSummary, RuntimeInfo, TraceSealRuntimeError } from "./types";
import { validateRunId } from "./validation";

export type DashboardOperation = "latest" | "list" | "run" | "policy";
export type DashboardArgMode = "python-module" | "bundled-core";

export interface PythonCommandSpec {
  command: string;
  baseArgs: string[];
}

export interface TraceSealCommandSpec extends PythonCommandSpec {
  mode: DashboardArgMode;
}

export interface RunJsonCommandOptions {
  cwd: string;
  timeoutMs?: number;
  env?: NodeJS.ProcessEnv;
  spawnImpl?: typeof spawn;
}

export interface PythonRunnerOptions {
  repositoryRoot?: string;
  python?: PythonCommandSpec;
  timeoutMs?: number;
  spawnImpl?: typeof spawn;
  env?: NodeJS.ProcessEnv;
  isPackaged?: boolean;
  resourcesPath?: string;
  coreExecutablePath?: string;
}

export function buildDashboardArgs(operation: DashboardOperation, runId?: string): string[] {
  return buildDashboardArgsForMode("python-module", operation, runId);
}

export function buildDashboardArgsForMode(mode: DashboardArgMode, operation: DashboardOperation, runId?: string): string[] {
  const base = mode === "python-module" ? ["-m", "traceseal", "dashboard-data"] : ["dashboard-data"];
  switch (operation) {
    case "latest":
      return [...base, "latest"];
    case "list":
      return [...base, "list"];
    case "policy":
      return [...base, "policy"];
    case "run":
      return [...base, "run", validateRunId(runId)];
    default: {
      const neverOperation: never = operation;
      throw new TraceSealRuntimeError("INTERNAL_ERROR", `unsupported operation: ${neverOperation}`);
    }
  }
}

export function parsePythonCommand(value: string): PythonCommandSpec {
  const parts = value.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    throw new TraceSealRuntimeError("PYTHON_NOT_FOUND", "empty Python command");
  }
  return { command: parts[0], baseArgs: parts.slice(1) };
}

export function defaultPythonCandidates(env: NodeJS.ProcessEnv = process.env): PythonCommandSpec[] {
  const configured = env.TRACESEAL_PYTHON_COMMAND || env.PYTHON;
  if (configured) {
    return [parsePythonCommand(configured)];
  }
  return [
    { command: "python", baseArgs: [] },
    { command: "python3", baseArgs: [] },
    { command: "py", baseArgs: ["-3"] },
  ];
}

export function findRepositoryRoot(startDir?: string): string {
  const seed = process.env.TRACESEAL_REPOSITORY_ROOT || startDir || process.cwd();
  let current = path.resolve(seed);
  if (fs.existsSync(current) && fs.statSync(current).isFile()) {
    current = path.dirname(current);
  }
  while (true) {
    if (fs.existsSync(path.join(current, "pyproject.toml")) && fs.existsSync(path.join(current, "traceseal"))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return path.resolve(seed);
    }
    current = parent;
  }
}

export function packagedRepositoryRoot(env: NodeJS.ProcessEnv = process.env, cwd: string = process.cwd()): string {
  const configured = env.TRACESEAL_REPOSITORY_ROOT;
  if (configured) {
    return path.resolve(configured);
  }
  return path.resolve(cwd);
}

function normalizeEnv(env?: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
  return {
    ...process.env,
    ...(env || {}),
    PYTHONIOENCODING: "utf-8",
  };
}

export function runRawCommand(
  command: string,
  args: string[],
  options: RunJsonCommandOptions,
): Promise<{ stdout: string; stderr: string; exitCode: number | null }> {
  const timeoutMs = options.timeoutMs ?? 10_000;
  const spawnImpl = options.spawnImpl || spawn;
  const spawnOptions: SpawnOptionsWithoutStdio = {
    cwd: options.cwd,
    env: normalizeEnv(options.env),
    shell: false,
    windowsHide: true,
  };

  return new Promise((resolve, reject) => {
    let child;
    try {
      child = spawnImpl(command, args, spawnOptions);
    } catch (error) {
      reject(new TraceSealRuntimeError("PYTHON_NOT_FOUND", `failed to start command: ${command}`, error));
      return;
    }

    let stdout = "";
    let stderr = "";
    let settled = false;
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      try {
        child.kill();
      } catch {
        // ignore kill failures; close/error handlers will settle the promise
      }
    }, timeoutMs);

    child.stdout?.setEncoding("utf8");
    child.stderr?.setEncoding("utf8");
    child.stdout?.on("data", (chunk: string | Buffer) => {
      stdout += chunk.toString();
    });
    child.stderr?.on("data", (chunk: string | Buffer) => {
      stderr += chunk.toString();
    });
    child.once("error", (error: NodeJS.ErrnoException) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      const code = error.code === "ENOENT" ? "PYTHON_NOT_FOUND" : "INTERNAL_ERROR";
      reject(new TraceSealRuntimeError(code, `failed to start command: ${command}`, error));
    });
    child.once("close", (exitCode: number | null) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (timedOut) {
        reject(new TraceSealRuntimeError("TIMEOUT", `command timed out after ${timeoutMs}ms`, { command, args }));
        return;
      }
      resolve({ stdout, stderr, exitCode });
    });
  });
}

function parseJsonPayload(stdout: string): unknown {
  try {
    return JSON.parse(stdout);
  } catch (error) {
    throw new TraceSealRuntimeError("INVALID_JSON", "Python command returned invalid JSON", { stdout, error });
  }
}

function maybePythonError(payload: unknown): TraceSealRuntimeError | null {
  if (payload && typeof payload === "object" && "ok" in payload && (payload as { ok?: unknown }).ok === false) {
    const error = (payload as { error?: { code?: string; message?: string; details?: unknown } }).error || {};
    const code = (error.code || "COMMAND_FAILED") as TraceSealRuntimeError["code"];
    return new TraceSealRuntimeError(code, error.message || "Python command failed", error.details);
  }
  return null;
}

export async function runJsonCommand(command: string, args: string[], options: RunJsonCommandOptions): Promise<unknown> {
  const result = await runRawCommand(command, args, options);
  if (result.exitCode !== 0) {
    const payload = result.stdout.trim() ? parseJsonPayload(result.stdout) : null;
    const pythonError = payload ? maybePythonError(payload) : null;
    if (pythonError) {
      throw pythonError;
    }
    throw new TraceSealRuntimeError("COMMAND_FAILED", `command failed with exit code ${result.exitCode}`, {
      command,
      args,
      exitCode: result.exitCode,
      stderr: result.stderr,
      stdout: result.stdout,
    });
  }
  const payload = parseJsonPayload(result.stdout);
  const pythonError = maybePythonError(payload);
  if (pythonError) {
    throw pythonError;
  }
  return payload;
}

export async function detectPythonCommand(options: PythonRunnerOptions = {}): Promise<PythonCommandSpec> {
  if (options.python) {
    return options.python;
  }
  const repositoryRoot = options.repositoryRoot || findRepositoryRoot();
  const candidates = defaultPythonCandidates(options.env);
  for (const candidate of candidates) {
    try {
      const result = await runRawCommand(candidate.command, [...candidate.baseArgs, "--version"], {
        cwd: repositoryRoot,
        timeoutMs: options.timeoutMs ?? 3000,
        spawnImpl: options.spawnImpl,
        env: options.env,
      });
      if (result.exitCode === 0) {
        return candidate;
      }
    } catch {
      // try next candidate
    }
  }
  throw new TraceSealRuntimeError("PYTHON_NOT_FOUND", "No usable Python command found");
}

export function packagedCoreCommand(options: PythonRunnerOptions = {}): TraceSealCommandSpec {
  const corePath = options.coreExecutablePath || bundledCoreExecutablePath({ resourcesPath: options.resourcesPath });
  if (!fs.existsSync(corePath)) {
    throw new TraceSealRuntimeError("PYTHON_NOT_FOUND", `Bundled TraceSeal core executable not found: ${corePath}`, {
      corePath,
    });
  }
  return { command: corePath, baseArgs: [], mode: "bundled-core" };
}

export async function resolveTraceSealCommand(options: PythonRunnerOptions = {}): Promise<TraceSealCommandSpec> {
  if (options.isPackaged) {
    return packagedCoreCommand(options);
  }
  const python = await detectPythonCommand(options);
  return { ...python, mode: "python-module" };
}

export class PythonDashboardRunner {
  private repositoryRoot: string;
  private readonly timeoutMs: number;
  private readonly python?: PythonCommandSpec;
  private readonly spawnImpl?: typeof spawn;
  private readonly env?: NodeJS.ProcessEnv;
  private readonly isPackaged?: boolean;
  private readonly resourcesPath?: string;
  private readonly coreExecutablePath?: string;

  constructor(options: PythonRunnerOptions = {}) {
    this.repositoryRoot =
      options.repositoryRoot ||
      (options.isPackaged ? packagedRepositoryRoot(options.env) : findRepositoryRoot(__dirname));
    this.timeoutMs = options.timeoutMs ?? 15_000;
    this.python = options.python;
    this.spawnImpl = options.spawnImpl;
    this.env = options.env;
    this.isPackaged = options.isPackaged;
    this.resourcesPath = options.resourcesPath;
    this.coreExecutablePath = options.coreExecutablePath;
  }

  setRepositoryRoot(repositoryRoot: string): void {
    this.repositoryRoot = path.resolve(repositoryRoot);
  }

  getRepositoryRoot(): string {
    return this.repositoryRoot;
  }

  private async commandSpec(): Promise<TraceSealCommandSpec> {
    return resolveTraceSealCommand({
      repositoryRoot: this.repositoryRoot,
      python: this.python,
      timeoutMs: this.timeoutMs,
      spawnImpl: this.spawnImpl,
      env: this.env,
      isPackaged: this.isPackaged,
      resourcesPath: this.resourcesPath,
      coreExecutablePath: this.coreExecutablePath,
    });
  }

  private async run(operation: DashboardOperation, runId?: string): Promise<unknown> {
    const spec = await this.commandSpec();
    const args = [...spec.baseArgs, ...buildDashboardArgsForMode(spec.mode, operation, runId)];
    return runJsonCommand(spec.command, args, {
      cwd: this.repositoryRoot,
      timeoutMs: this.timeoutMs,
      spawnImpl: this.spawnImpl,
      env: this.env,
    });
  }

  async getLatestRun(): Promise<DashboardRunExport> {
    return (await this.run("latest")) as DashboardRunExport;
  }

  async listRuns(): Promise<RunSummary[]> {
    const payload = (await this.run("list")) as { runs?: RunSummary[] };
    return payload.runs || [];
  }

  async getRun(runId: string): Promise<DashboardRunExport> {
    return (await this.run("run", validateRunId(runId))) as DashboardRunExport;
  }

  async getPolicy(): Promise<PolicyRule[]> {
    const payload = (await this.run("policy")) as { rules?: PolicyRule[] };
    return payload.rules || [];
  }

  async getRuntimeInfo(): Promise<RuntimeInfo> {
    const spec = await this.commandSpec();
    let version: string | undefined;
    if (spec.mode === "bundled-core") {
      version = "bundled traceseal-core";
    } else {
      try {
        const result = await runRawCommand(spec.command, [...spec.baseArgs, "--version"], {
          cwd: this.repositoryRoot,
          timeoutMs: 3000,
          spawnImpl: this.spawnImpl,
          env: this.env,
        });
        version = (result.stdout || result.stderr).trim();
      } catch {
        version = undefined;
      }
    }
    return {
      pythonCommand: [spec.command, ...spec.baseArgs].join(" "),
      repositoryRoot: this.repositoryRoot,
      platform: os.platform(),
      version,
    };
  }
}
