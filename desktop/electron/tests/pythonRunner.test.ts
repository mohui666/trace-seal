import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  buildDashboardArgs,
  buildDashboardArgsForMode,
  packagedCoreCommand,
  packagedRepositoryRoot,
  parsePythonCommand,
  resolveTraceSealCommand,
  runJsonCommand,
  PythonDashboardRunner,
} from "../src/pythonRunner";
import { TraceSealRuntimeError } from "../src/types";
import { validateRunId } from "../src/validation";

test("buildDashboardArgs constructs fixed Python CLI args", () => {
  assert.deepEqual(buildDashboardArgs("latest"), ["-m", "traceseal", "dashboard-data", "latest"]);
  assert.deepEqual(buildDashboardArgs("list"), ["-m", "traceseal", "dashboard-data", "list"]);
  assert.deepEqual(buildDashboardArgs("policy"), ["-m", "traceseal", "dashboard-data", "policy"]);
  assert.deepEqual(buildDashboardArgs("run", "run_20260617_000000_000000"), [
    "-m",
    "traceseal",
    "dashboard-data",
    "run",
    "run_20260617_000000_000000",
  ]);
});

test("buildDashboardArgsForMode constructs bundled core args without Python module prefix", () => {
  assert.deepEqual(buildDashboardArgsForMode("bundled-core", "latest"), ["dashboard-data", "latest"]);
  assert.deepEqual(buildDashboardArgsForMode("bundled-core", "list"), ["dashboard-data", "list"]);
  assert.deepEqual(buildDashboardArgsForMode("bundled-core", "policy"), ["dashboard-data", "policy"]);
  assert.deepEqual(buildDashboardArgsForMode("bundled-core", "run", "run_20260617_000000_000000"), [
    "dashboard-data",
    "run",
    "run_20260617_000000_000000",
  ]);
});

test("parsePythonCommand preserves command plus base args without shell", () => {
  assert.deepEqual(parsePythonCommand("py -3"), { command: "py", baseArgs: ["-3"] });
  assert.deepEqual(parsePythonCommand("python"), { command: "python", baseArgs: [] });
});

test("packagedCoreCommand resolves executable under process resourcesPath", async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "traceseal-core-"));
  const coreDir = path.join(tmp, "traceseal-core");
  fs.mkdirSync(coreDir, { recursive: true });
  const corePath = path.join(coreDir, process.platform === "win32" ? "traceseal-core.exe" : "traceseal-core");
  fs.writeFileSync(corePath, "", "utf8");
  const spec = packagedCoreCommand({ resourcesPath: tmp });
  assert.equal(spec.command, corePath);
  assert.deepEqual(spec.baseArgs, []);
  assert.equal(spec.mode, "bundled-core");
  fs.rmSync(tmp, { recursive: true, force: true });
});

test("packagedCoreCommand reports missing PyInstaller executable", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "traceseal-missing-core-"));
  assert.throws(
    () => packagedCoreCommand({ resourcesPath: tmp }),
    (error: unknown) => error instanceof TraceSealRuntimeError && error.code === "PYTHON_NOT_FOUND",
  );
  fs.rmSync(tmp, { recursive: true, force: true });
});

test("resolveTraceSealCommand uses bundled core in packaged mode", async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "traceseal-packaged-resources-"));
  const coreDir = path.join(tmp, "traceseal-core");
  fs.mkdirSync(coreDir, { recursive: true });
  const corePath = path.join(coreDir, process.platform === "win32" ? "traceseal-core.exe" : "traceseal-core");
  fs.writeFileSync(corePath, "", "utf8");
  const spec = await resolveTraceSealCommand({ isPackaged: true, resourcesPath: tmp });
  assert.equal(spec.command, corePath);
  assert.equal(spec.mode, "bundled-core");
  fs.rmSync(tmp, { recursive: true, force: true });
});

test("packagedRepositoryRoot prefers TRACESEAL_REPOSITORY_ROOT over packaged cwd", () => {
  const configured = path.join(os.tmpdir(), "TraceSeal Project With Spaces");
  assert.equal(packagedRepositoryRoot({ TRACESEAL_REPOSITORY_ROOT: configured } as NodeJS.ProcessEnv, "C:\\ignored"), path.resolve(configured));
  assert.equal(packagedRepositoryRoot({} as NodeJS.ProcessEnv, configured), path.resolve(configured));
});

test("PythonDashboardRunner switches repository root without rebuilding the runner", () => {
  const first = path.join(os.tmpdir(), "trace workspace one");
  const second = path.join(os.tmpdir(), "跟踪 工作区 two");
  const runner = new PythonDashboardRunner({ repositoryRoot: first });
  assert.equal(runner.getRepositoryRoot(), path.resolve(first));
  runner.setRepositoryRoot(second);
  assert.equal(runner.getRepositoryRoot(), path.resolve(second));
});

test("runJsonCommand parses JSON stdout", async () => {
  const payload = await runJsonCommand(process.execPath, ["-e", "console.log(JSON.stringify({ ok: true, value: 42 }))"], {
    cwd: process.cwd(),
    timeoutMs: 2000,
  });
  assert.deepEqual(payload, { ok: true, value: 42 });
});

test("runJsonCommand reports non-zero exit as COMMAND_FAILED", async () => {
  await assert.rejects(
    runJsonCommand(process.execPath, ["-e", "process.stderr.write('boom'); process.exit(7)"], {
      cwd: process.cwd(),
      timeoutMs: 2000,
    }),
    (error: unknown) => error instanceof TraceSealRuntimeError && error.code === "COMMAND_FAILED",
  );
});

test("runJsonCommand reports invalid JSON", async () => {
  await assert.rejects(
    runJsonCommand(process.execPath, ["-e", "console.log('not-json')"], {
      cwd: process.cwd(),
      timeoutMs: 2000,
    }),
    (error: unknown) => error instanceof TraceSealRuntimeError && error.code === "INVALID_JSON",
  );
});


test("runJsonCommand reports missing command as PYTHON_NOT_FOUND", async () => {
  await assert.rejects(
    runJsonCommand("definitely-not-a-python-command-traceseal", ["--version"], {
      cwd: process.cwd(),
      timeoutMs: 500,
    }),
    (error: unknown) => error instanceof TraceSealRuntimeError && error.code === "PYTHON_NOT_FOUND",
  );
});

test("runJsonCommand reports timeout", async () => {
  await assert.rejects(
    runJsonCommand(process.execPath, ["-e", "setTimeout(() => {}, 1000)"], {
      cwd: process.cwd(),
      timeoutMs: 50,
    }),
    (error: unknown) => error instanceof TraceSealRuntimeError && error.code === "TIMEOUT",
  );
});

test("validateRunId accepts only safe run identifiers", () => {
  assert.equal(validateRunId("run_20260617_000000_000000"), "run_20260617_000000_000000");
  for (const bad of ["", "latest", "../run_1", "run_../../x", "runs/latest", "C:/tmp/run_1"]) {
    assert.throws(() => validateRunId(bad), (error: unknown) => error instanceof TraceSealRuntimeError && error.code === "INVALID_RUN_ID");
  }
});
