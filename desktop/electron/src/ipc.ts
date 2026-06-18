import { validateRunId } from "./validation";

export const IPC_CHANNELS = {
  getLatestRun: "traceseal:getLatestRun",
  listRuns: "traceseal:listRuns",
  getRun: "traceseal:getRun",
  getPolicy: "traceseal:getPolicy",
  getRuntimeInfo: "traceseal:getRuntimeInfo",
  selectWorkspace: "traceseal:selectWorkspace",
  getWorkspace: "traceseal:getWorkspace",
  clearWorkspace: "traceseal:clearWorkspace",
} as const;

export interface IpcMainLike {
  handle(channel: string, listener: (event: unknown, ...args: unknown[]) => Promise<unknown> | unknown): void;
}

export interface TraceSealRunnerLike {
  getLatestRun(): Promise<unknown>;
  listRuns(): Promise<unknown>;
  getRun(runId: string): Promise<unknown>;
  getPolicy(): Promise<unknown>;
  getRuntimeInfo(): Promise<unknown>;
}

export interface WorkspaceControllerLike {
  selectWorkspace(): Promise<unknown>;
  getWorkspace(): Promise<unknown> | unknown;
  clearWorkspace(): Promise<unknown> | unknown;
}

export function registerTraceSealIpc(
  ipcMain: IpcMainLike,
  runner: TraceSealRunnerLike,
  workspace: WorkspaceControllerLike,
): void {
  ipcMain.handle(IPC_CHANNELS.getLatestRun, async () => runner.getLatestRun());
  ipcMain.handle(IPC_CHANNELS.listRuns, async () => runner.listRuns());
  ipcMain.handle(IPC_CHANNELS.getRun, async (_event: unknown, runId: unknown) => runner.getRun(validateRunId(runId)));
  ipcMain.handle(IPC_CHANNELS.getPolicy, async () => runner.getPolicy());
  ipcMain.handle(IPC_CHANNELS.getRuntimeInfo, async () => runner.getRuntimeInfo());
  ipcMain.handle(IPC_CHANNELS.selectWorkspace, async () => workspace.selectWorkspace());
  ipcMain.handle(IPC_CHANNELS.getWorkspace, async () => workspace.getWorkspace());
  ipcMain.handle(IPC_CHANNELS.clearWorkspace, async () => workspace.clearWorkspace());
}
