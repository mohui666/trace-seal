import { contextBridge, ipcRenderer } from "electron";

// Electron enables the renderer sandbox by default. A sandboxed preload may
// import Electron's built-in module, but it cannot require neighbouring files
// such as ./preloadApi. Keep this entrypoint self-contained so it works both
// from the development tree and from app.asar in the packaged application.
const traceSealApi = Object.freeze({
  getLatestRun: () => ipcRenderer.invoke("traceseal:getLatestRun"),
  listRuns: () => ipcRenderer.invoke("traceseal:listRuns"),
  getRun: (runId: string) => ipcRenderer.invoke("traceseal:getRun", runId),
  getPolicy: () => ipcRenderer.invoke("traceseal:getPolicy"),
  getRuntimeInfo: () => ipcRenderer.invoke("traceseal:getRuntimeInfo"),
  selectWorkspace: () => ipcRenderer.invoke("traceseal:selectWorkspace"),
  getWorkspace: () => ipcRenderer.invoke("traceseal:getWorkspace"),
  clearWorkspace: () => ipcRenderer.invoke("traceseal:clearWorkspace"),
});

contextBridge.exposeInMainWorld(
  "traceSeal",
  traceSealApi,
);
