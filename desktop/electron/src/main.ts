import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { app, BrowserWindow, dialog, ipcMain } from "electron";
import { registerTraceSealIpc } from "./ipc";
import { PythonDashboardRunner } from "./pythonRunner";
import { preloadPath, rendererIndexPath } from "./runtimePaths";
import { findRepositoryRoot } from "./pythonRunner";
import { planSquirrelStartup, squirrelShortcutArgs } from "./squirrel";
import { WorkspaceController, WorkspaceStore } from "./workspace";

// Handle Squirrel.Windows install / update / uninstall lifecycle events.
// On these events the app must exit immediately (before app.whenReady()) so
// Update.exe can finalize the install / remove bundled files on uninstall.
// Update.exe does not auto-create Start Menu / Desktop shortcuts in this build,
// so on install/update we ask it to create them, and on uninstall to remove
// them. The Update.exe call is detached so it does not block the app exit that
// Squirrel's installer is waiting for. --squirrel-firstrun and ordinary
// launches fall through and run normally.
const squirrelPlan = planSquirrelStartup();
if (squirrelPlan.shouldQuit) {
  const args = squirrelShortcutArgs(squirrelPlan.shortcutAction, squirrelPlan.layout.shortcutTarget);
  if (args && fs.existsSync(squirrelPlan.layout.updateExe)) {
    try {
      spawn(squirrelPlan.layout.updateExe, args, { detached: true, stdio: "ignore" }).unref();
    } catch {
      // Best effort: shortcut creation must not block the Squirrel lifecycle.
    }
  }
  app.quit();
}

function rendererUrl(): string | null {
  return process.env.TRACESEAL_RENDERER_URL || null;
}

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: preloadPath(__dirname),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devUrl = rendererUrl();
  if (devUrl) {
    void win.loadURL(devUrl);
    return;
  }

  const rendererIndex = rendererIndexPath({
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
    dirname: __dirname,
    cwd: process.cwd(),
    env: process.env,
  });
  if (rendererIndex) {
    void win.loadFile(rendererIndex);
    return;
  }

  void win.loadURL(
    "data:text/html;charset=utf-8," +
      encodeURIComponent(
        "<h1>TraceSeal Dashboard runtime ready</h1><p>Renderer dist not found. Run npm run build in desktop/renderer.</p>",
      ),
  );
}

app.whenReady().then(() => {
  const fallbackRoot = app.isPackaged ? process.cwd() : findRepositoryRoot(__dirname);
  const runner = new PythonDashboardRunner({
    repositoryRoot: fallbackRoot,
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
  });
  const workspace = new WorkspaceController(
    new WorkspaceStore(path.join(app.getPath("userData"), "settings.json")),
    runner,
    async () => {
      const result = await dialog.showOpenDialog({ properties: ["openDirectory"] });
      return result.canceled ? null : result.filePaths[0] || null;
    },
    fallbackRoot,
  );
  registerTraceSealIpc(ipcMain, runner, workspace);
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
