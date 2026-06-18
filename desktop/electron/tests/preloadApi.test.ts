import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { createTraceSealApi } from "../src/preloadApi";
import { IPC_CHANNELS } from "../src/ipc";

test("preload API exposes only the approved TraceSeal methods", () => {
  const api = createTraceSealApi(async () => ({}));
  assert.deepEqual(Object.keys(api).sort(), [
    "getLatestRun", "getPolicy", "getRun", "getRuntimeInfo", "listRuns",
    "selectWorkspace", "getWorkspace", "clearWorkspace",
  ].sort());
  assert.equal(Object.isFrozen(api), true);
});

test("preload API invokes fixed IPC channels", async () => {
  const calls: Array<[string, unknown[]]> = [];
  const api = createTraceSealApi(async (channel, ...args) => {
    calls.push([channel, args]);
    return { channel, args };
  });
  await api.getLatestRun();
  await api.listRuns();
  await api.getRun("run_20260617_000000_000000");
  await api.getPolicy();
  await api.getRuntimeInfo();
  await api.selectWorkspace();
  await api.getWorkspace();
  await api.clearWorkspace();
  assert.deepEqual(calls, [
    [IPC_CHANNELS.getLatestRun, []],
    [IPC_CHANNELS.listRuns, []],
    [IPC_CHANNELS.getRun, ["run_20260617_000000_000000"]],
    [IPC_CHANNELS.getPolicy, []],
    [IPC_CHANNELS.getRuntimeInfo, []],
    [IPC_CHANNELS.selectWorkspace, []],
    [IPC_CHANNELS.getWorkspace, []],
    [IPC_CHANNELS.clearWorkspace, []],
  ]);
});

test("compiled preload is self-contained for the Electron sandbox", () => {
  const compiledPreload = fs.readFileSync(
    path.resolve(process.cwd(), "dist", "src", "preload.js"),
    "utf8",
  );
  assert.doesNotMatch(compiledPreload, /require\(["']\.\//);
  assert.match(compiledPreload, /require\(["']electron["']\)/);
  for (const channel of Object.values(IPC_CHANNELS)) {
    assert.ok(compiledPreload.includes(channel), `missing fixed IPC channel ${channel}`);
  }
});
