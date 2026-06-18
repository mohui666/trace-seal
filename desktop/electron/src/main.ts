import { app, BrowserWindow, ipcMain } from "electron";
import { registerTraceSealIpc } from "./ipc";
import { PythonDashboardRunner } from "./pythonRunner";
import { preloadPath, rendererIndexPath } from "./runtimePaths";

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

registerTraceSealIpc(
  ipcMain,
  new PythonDashboardRunner({
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
  }),
);

app.whenReady().then(() => {
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
