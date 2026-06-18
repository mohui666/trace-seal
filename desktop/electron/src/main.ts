import path from "node:path";
import { app, BrowserWindow, dialog, ipcMain } from "electron";
import { registerTraceSealIpc } from "./ipc";
import { PythonDashboardRunner } from "./pythonRunner";
import { preloadPath, rendererIndexPath } from "./runtimePaths";
import { findRepositoryRoot } from "./pythonRunner";
import { WorkspaceController, WorkspaceStore } from "./workspace";

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
