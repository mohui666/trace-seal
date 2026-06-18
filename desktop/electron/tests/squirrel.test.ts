import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";
import {
  planSquirrelStartup,
  resolveSquirrelLayout,
  shouldQuitForSquirrelStartup,
  squirrelEvent,
  squirrelShortcutAction,
  squirrelShortcutArgs,
} from "../src/squirrel";

// Squirrel relaunches the app as `<exe> --squirrel-<event> [version]`, so the
// event flag lives in argv[1]. argv[0] is the executable path.

test("squirrelEvent returns the --squirrel-* flag from argv[1]", () => {
  assert.equal(squirrelEvent(["C:\\app\\TraceSeal.exe", "--squirrel-install", "0.2.0"]), "--squirrel-install");
  assert.equal(squirrelEvent(["C:\\app\\TraceSeal.exe", "--squirrel-uninstall", "0.2.0"]), "--squirrel-uninstall");
});

test("squirrelEvent ignores non-squirrel argv", () => {
  assert.equal(squirrelEvent(["C:\\app\\TraceSeal.exe", "--remote-debugging-port=9222"]), null);
  assert.equal(squirrelEvent(["C:\\app\\TraceSeal.exe"]), null);
  assert.equal(squirrelEvent([]), null);
});

test("shouldQuitForSquirrelStartup is true for install/update/uninstall/obsolete", () => {
  for (const evt of ["--squirrel-install", "--squirrel-updated", "--squirrel-uninstall", "--squirrel-obsolete"]) {
    assert.equal(shouldQuitForSquirrelStartup(["C:\\app\\TraceSeal.exe", evt, "0.2.0"]), true, `${evt} should quit`);
  }
});

test("shouldQuitForSquirrelStartup is false for --squirrel-firstrun and ordinary launches", () => {
  assert.equal(shouldQuitForSquirrelStartup(["C:\\app\\TraceSeal.exe", "--squirrel-firstrun"]), false);
  assert.equal(shouldQuitForSquirrelStartup(["C:\\app\\TraceSeal.exe"]), false);
  assert.equal(shouldQuitForSquirrelStartup(["C:\\app\\TraceSeal.exe", "--disable-gpu"]), false);
});

test("squirrelShortcutAction maps events to create / remove / none", () => {
  assert.equal(squirrelShortcutAction("--squirrel-install"), "create");
  assert.equal(squirrelShortcutAction("--squirrel-updated"), "create");
  assert.equal(squirrelShortcutAction("--squirrel-uninstall"), "remove");
  assert.equal(squirrelShortcutAction("--squirrel-obsolete"), "none");
  assert.equal(squirrelShortcutAction("--squirrel-firstrun"), "none");
  assert.equal(squirrelShortcutAction(null), "none");
});

test("squirrelShortcutArgs builds Update.exe argv for create and remove", () => {
  assert.deepEqual(squirrelShortcutArgs("create", "C:\\traceseal\\TraceSeal.exe"), [
    "--createShortcut",
    "C:\\traceseal\\TraceSeal.exe",
  ]);
  assert.deepEqual(squirrelShortcutArgs("remove", "C:\\traceseal\\TraceSeal.exe"), [
    "--removeShortcut",
    "C:\\traceseal\\TraceSeal.exe",
  ]);
  assert.equal(squirrelShortcutArgs("none", "x"), null);
});

test("resolveSquirrelLayout resolves Update.exe and the stub one level above the app-<ver> dir", () => {
  const layout = resolveSquirrelLayout("C:\\Users\\me\\AppData\\Local\\traceseal\\app-0.2.0\\TraceSeal.exe");
  assert.equal(layout.updateExe, path.join("C:\\Users\\me\\AppData\\Local\\traceseal", "Update.exe"));
  assert.equal(layout.shortcutTarget, path.join("C:\\Users\\me\\AppData\\Local\\traceseal", "TraceSeal.exe"));
});

test("resolveSquirrelLayout treats the stub dir itself as the install root", () => {
  // When launched from the stub (no app-<ver> parent), install root is its dir.
  const layout = resolveSquirrelLayout("C:\\Users\\me\\AppData\\Local\\traceseal\\TraceSeal.exe");
  assert.equal(layout.updateExe, path.join("C:\\Users\\me\\AppData\\Local\\traceseal", "Update.exe"));
  assert.equal(layout.shortcutTarget, path.join("C:\\Users\\me\\AppData\\Local\\traceseal", "TraceSeal.exe"));
});

test("planSquirrelStartup quits + creates shortcuts on --squirrel-install", () => {
  const plan = planSquirrelStartup(
    "C:\\Users\\me\\AppData\\Local\\traceseal\\app-0.2.0\\TraceSeal.exe",
    ["C:\\Users\\me\\AppData\\Local\\traceseal\\app-0.2.0\\TraceSeal.exe", "--squirrel-install", "0.2.0"],
  );
  assert.equal(plan.shouldQuit, true);
  assert.equal(plan.shortcutAction, "create");
  assert.equal(plan.layout.shortcutTarget, path.join("C:\\Users\\me\\AppData\\Local\\traceseal", "TraceSeal.exe"));
});

test("planSquirrelStartup quits + removes shortcuts on --squirrel-uninstall", () => {
  const plan = planSquirrelStartup(
    "C:\\Users\\me\\AppData\\Local\\traceseal\\app-0.2.0\\TraceSeal.exe",
    ["C:\\Users\\me\\AppData\\Local\\traceseal\\app-0.2.0\\TraceSeal.exe", "--squirrel-uninstall", "0.2.0"],
  );
  assert.equal(plan.shouldQuit, true);
  assert.equal(plan.shortcutAction, "remove");
});

test("planSquirrelStartup quits with no shortcut action on --squirrel-obsolete", () => {
  const plan = planSquirrelStartup("C:\\app\\TraceSeal.exe", ["C:\\app\\TraceSeal.exe", "--squirrel-obsolete"]);
  assert.equal(plan.shouldQuit, true);
  assert.equal(plan.shortcutAction, "none");
});

test("planSquirrelStartup does not quit on a normal launch", () => {
  const plan = planSquirrelStartup("C:\\app\\TraceSeal.exe", ["C:\\app\\TraceSeal.exe", "--disable-gpu"]);
  assert.equal(plan.shouldQuit, false);
  assert.equal(plan.shortcutAction, "none");
});
