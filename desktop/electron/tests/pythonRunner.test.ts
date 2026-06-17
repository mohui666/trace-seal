import assert from "node:assert/strict";
import test from "node:test";
import { buildDashboardArgs, parsePythonCommand, runJsonCommand } from "../src/pythonRunner";
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

test("parsePythonCommand preserves command plus base args without shell", () => {
  assert.deepEqual(parsePythonCommand("py -3"), { command: "py", baseArgs: ["-3"] });
  assert.deepEqual(parsePythonCommand("python"), { command: "python", baseArgs: [] });
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
