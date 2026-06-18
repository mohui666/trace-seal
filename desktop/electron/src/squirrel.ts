// Squirrel.Windows lifecycle handling.
//
// When Squirrel installs / updates / uninstalls the app it relaunches the
// executable with a leading `--squirrel-*` argument (e.g.
// `TraceSeal.exe --squirrel-install 0.2.0`). On those events the app MUST exit
// immediately so that Squirrel's Update.exe can finish deleting the bundled
// files on uninstall. `--squirrel-firstrun` (and ordinary launches) are normal
// user launches and must NOT exit.
//
// In this Squirrel.Windows + Forge build, Update.exe does NOT auto-create Start
// Menu / Desktop shortcuts during install (verified empirically: the install
// log contains no shortcut step). The app is therefore responsible for asking
// Update.exe to create shortcuts on install/update and remove them on
// uninstall. Update.exe's `--createShortcut` / `--removeShortcut` commands
// perform those operations.
//
// The planning helpers below are pure functions over argv / execPath so they
// can be unit-tested without spawning Electron or Update.exe. main.ts executes
// the resulting plan (spawning Update.exe, then app.quit()).

import path from "node:path";

/** Squirrel events on which the app should quit immediately. */
const QUIT_EVENTS: ReadonlySet<string> = new Set([
  "--squirrel-install",
  "--squirrel-updated",
  "--squirrel-uninstall",
  "--squirrel-obsolete",
]);

/** Squirrel events on which shortcuts should be created. */
const CREATE_SHORTCUT_EVENTS: ReadonlySet<string> = new Set([
  "--squirrel-install",
  "--squirrel-updated",
]);

/** Squirrel events on which shortcuts should be removed. */
const REMOVE_SHORTCUT_EVENTS: ReadonlySet<string> = new Set(["--squirrel-uninstall"]);

/** The Squirrel event flag carried in argv (e.g. `--squirrel-install`), or null. */
export function squirrelEvent(argv: readonly string[] = process.argv): string | null {
  const candidate = argv[1];
  if (typeof candidate === "string" && candidate.startsWith("--squirrel-")) {
    return candidate;
  }
  return null;
}

/** True when the process was launched for a Squirrel lifecycle event that must exit. */
export function shouldQuitForSquirrelStartup(argv: readonly string[] = process.argv): boolean {
  const event = squirrelEvent(argv);
  return event !== null && QUIT_EVENTS.has(event);
}

export type SquirrelShortcutAction = "create" | "remove" | "none";

/** What shortcut operation (if any) the event requires. */
export function squirrelShortcutAction(event: string | null): SquirrelShortcutAction {
  if (event && CREATE_SHORTCUT_EVENTS.has(event)) return "create";
  if (event && REMOVE_SHORTCUT_EVENTS.has(event)) return "remove";
  return "none";
}

export interface SquirrelLayout {
  /** Path to Update.exe at the Squirrel install root. */
  updateExe: string;
  /** Stub executable at the install root that shortcuts should target. */
  shortcutTarget: string;
}

/**
 * Resolve the Squirrel install layout from the running executable path.
 *
 * Squirrel runs the versioned app at `<installRoot>\app-<version>\<exe>` for
 * lifecycle events; the stable stub and Update.exe live one level up at
 * `<installRoot>`. When launched from the stub directly (no `app-` parent) the
 * install root is the executable's own directory.
 */
export function resolveSquirrelLayout(execPath: string = process.execPath): SquirrelLayout {
  const exeName = path.basename(execPath);
  const dir = path.dirname(execPath);
  const installRoot = path.basename(dir).startsWith("app-") ? path.dirname(dir) : dir;
  return {
    updateExe: path.join(installRoot, "Update.exe"),
    shortcutTarget: path.join(installRoot, exeName),
  };
}

/** Build the Update.exe argv for a shortcut action, or null for "none". */
export function squirrelShortcutArgs(action: SquirrelShortcutAction, target: string): string[] | null {
  if (action === "create") return ["--createShortcut", target];
  if (action === "remove") return ["--removeShortcut", target];
  return null;
}

export interface SquirrelStartupPlan {
  shouldQuit: boolean;
  shortcutAction: SquirrelShortcutAction;
  layout: SquirrelLayout;
}

/**
 * Pure plan for main.ts to execute: whether to quit, which shortcut action to
 * run, and the Update.exe / target paths to use.
 */
export function planSquirrelStartup(
  execPath: string = process.execPath,
  argv: readonly string[] = process.argv,
): SquirrelStartupPlan {
  const event = squirrelEvent(argv);
  return {
    shouldQuit: shouldQuitForSquirrelStartup(argv),
    shortcutAction: squirrelShortcutAction(event),
    layout: resolveSquirrelLayout(execPath),
  };
}
