import { PythonDashboardRunner } from "./pythonRunner";
import { validateRunId } from "./validation";

export const IPC_CHANNELS = {
  getLatestRun: "traceseal:getLatestRun",
  listRuns: "traceseal:listRuns",
  getRun: "traceseal:getRun",
  getPolicy: "traceseal:getPolicy",
  getRuntimeInfo: "traceseal:getRuntimeInfo",
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

export function registerTraceSealIpc(ipcMain: IpcMainLike, runner: TraceSealRunnerLike = new PythonDashboardRunner()): void {
  ipcMain.handle(IPC_CHANNELS.getLatestRun, async () => runner.getLatestRun());
  ipcMain.handle(IPC_CHANNELS.listRuns, async () => runner.listRuns());
  ipcMain.handle(IPC_CHANNELS.getRun, async (_event: unknown, runId: unknown) => runner.getRun(validateRunId(runId)));
  ipcMain.handle(IPC_CHANNELS.getPolicy, async () => runner.getPolicy());
  ipcMain.handle(IPC_CHANNELS.getRuntimeInfo, async () => runner.getRuntimeInfo());
}
