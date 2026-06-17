import { TraceSealApi } from "./types";
import { IPC_CHANNELS } from "./ipc";

export type IpcInvoker = (channel: string, ...args: unknown[]) => Promise<unknown>;

export function createTraceSealApi(invoke: IpcInvoker): TraceSealApi {
  return Object.freeze({
    getLatestRun: () => invoke(IPC_CHANNELS.getLatestRun) as Promise<ReturnType<TraceSealApi["getLatestRun"]> extends Promise<infer T> ? T : never>,
    listRuns: () => invoke(IPC_CHANNELS.listRuns) as Promise<ReturnType<TraceSealApi["listRuns"]> extends Promise<infer T> ? T : never>,
    getRun: (runId: string) => invoke(IPC_CHANNELS.getRun, runId) as Promise<ReturnType<TraceSealApi["getRun"]> extends Promise<infer T> ? T : never>,
    getPolicy: () => invoke(IPC_CHANNELS.getPolicy) as Promise<ReturnType<TraceSealApi["getPolicy"]> extends Promise<infer T> ? T : never>,
    getRuntimeInfo: () => invoke(IPC_CHANNELS.getRuntimeInfo) as Promise<ReturnType<TraceSealApi["getRuntimeInfo"]> extends Promise<infer T> ? T : never>,
  });
}
