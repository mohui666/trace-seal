import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { WorkspaceController, WorkspaceStore, inspectWorkspace } from "../src/workspace";

function fixture(name: string): { root: string; settings: string; cleanup(): void } {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), `traceseal-${name}-`));
  return {
    root,
    settings: path.join(root, "user-data", "settings.json"),
    cleanup: () => fs.rmSync(root, { recursive: true, force: true }),
  };
}

test("missing settings file returns an empty workspace", () => {
  const f = fixture("missing-settings");
  assert.deepEqual(new WorkspaceStore(f.settings).getWorkspace(), {
    path: null, valid: false, hasRuns: false, hasPolicy: false,
  });
  f.cleanup();
});

test("corrupt settings JSON safely returns an empty workspace", () => {
  const f = fixture("corrupt-settings");
  fs.mkdirSync(path.dirname(f.settings), { recursive: true });
  fs.writeFileSync(f.settings, "{not-json", "utf8");
  assert.equal(new WorkspaceStore(f.settings).getWorkspace().path, null);
  f.cleanup();
});

test("workspace is normalized, saved and read with runs and policy flags", () => {
  const f = fixture("save-read");
  const workspace = path.join(f.root, "project with spaces");
  fs.mkdirSync(path.join(workspace, "runs"), { recursive: true });
  fs.mkdirSync(path.join(workspace, "policy"), { recursive: true });
  const store = new WorkspaceStore(f.settings);
  assert.deepEqual(store.saveWorkspace(workspace), {
    path: path.resolve(workspace), valid: true, hasRuns: true, hasPolicy: true,
  });
  assert.deepEqual(store.getWorkspace(), {
    path: path.resolve(workspace), valid: true, hasRuns: true, hasPolicy: true,
  });
  f.cleanup();
});

test("workspace settings can be cleared", () => {
  const f = fixture("clear");
  const workspace = path.join(f.root, "workspace");
  fs.mkdirSync(workspace);
  const store = new WorkspaceStore(f.settings);
  store.saveWorkspace(workspace);
  store.clearWorkspace();
  assert.equal(fs.existsSync(f.settings), false);
  assert.equal(store.getWorkspace().path, null);
  f.cleanup();
});

test("deleted workspace is retained as an invalid path", () => {
  const f = fixture("deleted");
  const missing = path.join(f.root, "deleted-workspace");
  fs.mkdirSync(path.dirname(f.settings), { recursive: true });
  fs.writeFileSync(f.settings, JSON.stringify({ workspaceRoot: missing }), "utf8");
  assert.deepEqual(new WorkspaceStore(f.settings).getWorkspace(), {
    path: path.resolve(missing), valid: false, hasRuns: false, hasPolicy: false,
  });
  f.cleanup();
});

test("Unicode workspace paths are preserved", () => {
  const f = fixture("unicode");
  const workspace = path.join(f.root, "中文 工作区 🚀");
  fs.mkdirSync(workspace);
  const store = new WorkspaceStore(f.settings);
  store.saveWorkspace(workspace);
  assert.equal(store.getWorkspace().path, path.resolve(workspace));
  f.cleanup();
});

test("dialog cancellation keeps the current workspace", async () => {
  const f = fixture("cancel");
  const workspace = path.join(f.root, "workspace");
  fs.mkdirSync(workspace);
  const store = new WorkspaceStore(f.settings);
  store.saveWorkspace(workspace);
  const roots: string[] = [];
  const controller = new WorkspaceController(store, { setRepositoryRoot: (root) => roots.push(root) }, async () => null, f.root);
  const info = await controller.selectWorkspace();
  assert.equal(info.path, path.resolve(workspace));
  assert.equal(roots.at(-1), path.resolve(workspace));
  f.cleanup();
});

test("switching workspace updates the Python runner root", async () => {
  const f = fixture("switch");
  const workspace = path.join(f.root, "new workspace");
  fs.mkdirSync(workspace);
  const roots: string[] = [];
  const controller = new WorkspaceController(
    new WorkspaceStore(f.settings),
    { setRepositoryRoot: (root) => roots.push(root) },
    async () => workspace,
    f.root,
  );
  await controller.selectWorkspace();
  assert.equal(roots.at(-1), path.resolve(workspace));
  controller.clearWorkspace();
  assert.equal(roots.at(-1), path.resolve(f.root));
  f.cleanup();
});

test("workspace flags independently allow runs and policy to be absent", () => {
  const f = fixture("empty-workspace");
  const workspace = path.join(f.root, "empty");
  fs.mkdirSync(workspace);
  assert.deepEqual(inspectWorkspace(workspace), {
    path: path.resolve(workspace), valid: true, hasRuns: false, hasPolicy: false,
  });
  f.cleanup();
});
