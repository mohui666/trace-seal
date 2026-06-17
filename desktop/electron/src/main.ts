import path from "node:path";
import { app, BrowserWindow, ipcMain } from "electron";
import { registerTraceSealIpc } from "./ipc";

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

  const rendererIndex = path.resolve(__dirname, "../../renderer/index.html");
  void win.loadFile(rendererIndex).catch(() => {
    void win.loadURL("data:text/html;charset=utf-8,<h1>TraceSeal Dashboard runtime ready</h1>");
  });
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
