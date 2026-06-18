import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { bundledCoreExecutablePath, preloadPath, rendererIndexPath } from "../src/runtimePaths";

test("bundledCoreExecutablePath builds resources/traceseal-core executable path", () => {
  const resourcesPath = path.join(os.tmpdir(), "TraceSeal Resources 中文 With Spaces");
  const expectedName = process.platform === "win32" ? "traceseal-core.exe" : "traceseal-core";
  assert.equal(
    bundledCoreExecutablePath({ resourcesPath, platform: process.platform }),
    path.join(resourcesPath, "traceseal-core", expectedName),
  );
});

test("bundledCoreExecutablePath falls back to process.resourcesPath in packaged Electron", () => {
  const resourcesPath = path.join(os.tmpdir(), "TraceSeal Packaged Resources 中文");
  const expectedName = process.platform === "win32" ? "traceseal-core.exe" : "traceseal-core";
  const proc = process as NodeJS.Process & { resourcesPath?: string };
  const previous = proc.resourcesPath;
  proc.resourcesPath = resourcesPath;
  try {
    assert.equal(
      bundledCoreExecutablePath({ platform: process.platform }),
      path.join(resourcesPath, "traceseal-core", expectedName),
    );
  } finally {
    if (previous === undefined) {
      Reflect.deleteProperty(proc, "resourcesPath");
    } else {
      proc.resourcesPath = previous;
    }
  }
});

test("rendererIndexPath resolves packaged renderer dist under process.resourcesPath", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "traceseal-renderer-"));
  const rendererDir = path.join(tmp, "renderer");
  fs.mkdirSync(rendererDir, { recursive: true });
  const index = path.join(rendererDir, "index.html");
  fs.writeFileSync(index, "<!doctype html><title>TraceSeal</title>", "utf8");
  assert.equal(rendererIndexPath({ isPackaged: true, resourcesPath: tmp, env: {}, cwd: tmp, dirname: tmp }), index);
  fs.rmSync(tmp, { recursive: true, force: true });
});

test("rendererIndexPath supports explicit TRACESEAL_RENDERER_DIST override", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "traceseal-renderer-env-"));
  const index = path.join(tmp, "index.html");
  fs.writeFileSync(index, "<!doctype html><title>TraceSeal</title>", "utf8");
  assert.equal(rendererIndexPath({ env: { TRACESEAL_RENDERER_DIST: tmp } as NodeJS.ProcessEnv, cwd: tmp, dirname: tmp }), index);
  fs.rmSync(tmp, { recursive: true, force: true });
});

test("preloadPath resolves the compiled preload next to main process files", () => {
  assert.equal(preloadPath("C:\\TraceSeal\\dist\\src"), path.join("C:\\TraceSeal\\dist\\src", "preload.js"));
});
