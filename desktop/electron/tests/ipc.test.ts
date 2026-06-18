import assert from "node:assert/strict";
import test from "node:test";
import { IPC_CHANNELS, registerTraceSealIpc } from "../src/ipc";
import { TraceSealRuntimeError } from "../src/types";

class FakeIpcMain {
  handlers = new Map<string, (event: unknown, ...args: unknown[]) => Promise<unknown> | unknown>();
  handle(channel: string, listener: (event: unknown, ...args: unknown[]) => Promise<unknown> | unknown): void {
    this.handlers.set(channel, listener);
  }
}

test("registerTraceSealIpc maps fixed channels to runner methods", async () => {
  const calls: string[] = [];
  const runner = {
    async getLatestRun() {
      calls.push("latest");
      return { run_id: "run_latest" };
    },
    async listRuns() {
      calls.push("list");
      return [{ run_id: "run_1" }];
    },
    async getRun(runId: string) {
      calls.push(`run:${runId}`);
      return { run_id: runId };
    },
    async getPolicy() {
      calls.push("policy");
      return [{ rule_id: "dangerous_delete" }];
    },
    async getRuntimeInfo() {
      calls.push("runtime");
      return { pythonCommand: "python", repositoryRoot: "repo", platform: "test" };
    },
  };
  const ipc = new FakeIpcMain();
  const workspace = {
    async selectWorkspace() {
      calls.push("workspace:select");
      return { path: "repo", valid: true, hasRuns: true, hasPolicy: true };
    },
    getWorkspace() {
      calls.push("workspace:get");
      return { path: "repo", valid: true, hasRuns: true, hasPolicy: true };
    },
    clearWorkspace() {
      calls.push("workspace:clear");
    },
  };
  registerTraceSealIpc(ipc, runner, workspace);

  assert.deepEqual([...ipc.handlers.keys()].sort(), Object.values(IPC_CHANNELS).sort());
  assert.deepEqual(await ipc.handlers.get(IPC_CHANNELS.getLatestRun)?.({}, undefined), { run_id: "run_latest" });
  assert.deepEqual(await ipc.handlers.get(IPC_CHANNELS.listRuns)?.({}), [{ run_id: "run_1" }]);
  assert.deepEqual(await ipc.handlers.get(IPC_CHANNELS.getRun)?.({}, "run_20260617_000000_000000"), {
    run_id: "run_20260617_000000_000000",
  });
  assert.deepEqual(await ipc.handlers.get(IPC_CHANNELS.getPolicy)?.({}), [{ rule_id: "dangerous_delete" }]);
  assert.deepEqual(await ipc.handlers.get(IPC_CHANNELS.getRuntimeInfo)?.({}), {
    pythonCommand: "python",
    repositoryRoot: "repo",
    platform: "test",
  });
  assert.deepEqual(await ipc.handlers.get(IPC_CHANNELS.getWorkspace)?.({}), {
    path: "repo", valid: true, hasRuns: true, hasPolicy: true,
  });
  assert.deepEqual(await ipc.handlers.get(IPC_CHANNELS.selectWorkspace)?.({}), {
    path: "repo", valid: true, hasRuns: true, hasPolicy: true,
  });
  await ipc.handlers.get(IPC_CHANNELS.clearWorkspace)?.({});
  assert.deepEqual(calls, ["latest", "list", "run:run_20260617_000000_000000", "policy", "runtime", "workspace:get", "workspace:select", "workspace:clear"]);
});

test("getRun IPC rejects unsafe runId before runner is called", async () => {
  const ipc = new FakeIpcMain();
  const runner = {
    async getLatestRun() {},
    async listRuns() {},
    async getRun() {
      throw new Error("runner should not be called");
    },
    async getPolicy() {},
    async getRuntimeInfo() {},
  };
  const workspace = { async selectWorkspace() {}, getWorkspace() {}, clearWorkspace() {} };
  registerTraceSealIpc(ipc, runner, workspace);
  await assert.rejects(
    Promise.resolve(ipc.handlers.get(IPC_CHANNELS.getRun)?.({}, "../evil")),
    (error: unknown) => error instanceof TraceSealRuntimeError && error.code === "INVALID_RUN_ID",
  );
});
