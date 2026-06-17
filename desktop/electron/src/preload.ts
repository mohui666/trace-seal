import { contextBridge, ipcRenderer } from "electron";
import { createTraceSealApi } from "./preloadApi";

contextBridge.exposeInMainWorld(
  "traceSeal",
  createTraceSealApi((channel, ...args) => ipcRenderer.invoke(channel, ...args)),
);
