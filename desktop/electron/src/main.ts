import fs from "node:fs";
import path from "node:path";
import { app, BrowserWindow, ipcMain } from "electron";
import { registerTraceSealIpc } from "./ipc";

function rendererUrl(): string | null {
  return process.env.TRACESEAL_RENDERER_URL || null;
}

function rendererIndexPath(): string | null {
  if (process.env.TRACESEAL_RENDERER_DIST) {
    const explicit = path.resolve(process.env.TRACESEAL_RENDERER_DIST, "index.html");
    if (fs.existsSync(explicit)) return explicit;
  }

  const candidates = [
    // Compiled Electron runtime: desktop/electron/dist/src/main.js -> desktop/renderer/dist/index.html
    path.resolve(__dirname, "../../../renderer/dist/index.html"),
    // Fallback when running from source tooling.
    path.resolve(__dirname, "../../renderer/dist/index.html"),
    path.resolve(process.cwd(), "../renderer/dist/index.html"),
    path.resolve(process.cwd(), "desktop/renderer/dist/index.html"),
  ];

  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devUrl = rendererUrl();
  if (devUrl) {
    void win.loadURL(devUrl);
    return;
  }

  const rendererIndex = rendererIndexPath();
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

registerTraceSealIpc(ipcMain);

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
