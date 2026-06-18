declare module "electron" {
  export const app: {
    whenReady(): Promise<void>;
    on(event: string, listener: (...args: unknown[]) => void): void;
    quit(): void;
    getPath(name: string): string;
  };

  export class BrowserWindow {
    constructor(options: Record<string, unknown>);
    loadFile(path: string): Promise<void>;
    loadURL(url: string): Promise<void>;
    static getAllWindows(): BrowserWindow[];
  }

  export const ipcMain: {
    handle(channel: string, listener: (event: unknown, ...args: unknown[]) => Promise<unknown> | unknown): void;
  };

  export const contextBridge: {
    exposeInMainWorld(apiKey: string, api: unknown): void;
  };

  export const ipcRenderer: {
    invoke(channel: string, ...args: unknown[]): Promise<unknown>;
  };

  export const dialog: {
    showOpenDialog(options: { properties: string[] }): Promise<{ canceled: boolean; filePaths: string[] }>;
  };
}
