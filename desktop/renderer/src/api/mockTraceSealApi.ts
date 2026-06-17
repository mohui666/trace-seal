import type { TraceSealApi, DashboardRunExport, RunSummary, PolicyRule, RuntimeInfo } from './contracts';
import {
  deleteRun,
  envRun,
  gitRun,
  httpRun,
  cleanRun,
  failedRun,
  blockedRun,
  runSummaries,
  policyRules,
  runtimeInfo,
} from './fixtures';

const allRuns: Record<string, DashboardRunExport> = {
  'run-delete-001': deleteRun,
  'run-env-001': envRun,
  'run-git-001': gitRun,
  'run-http-001': httpRun,
  'run-clean-001': cleanRun,
  'run-failed-001': failedRun,
  'run-blocked-001': blockedRun,
};

let simulateError = false;
let simulateEmpty = false;

export function setMockErrorMode(on: boolean) {
  simulateError = on;
}

export function setMockEmptyMode(on: boolean) {
  simulateEmpty = on;
}

async function delay<T>(data: T, ms = 100): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms));
}

export const mockTraceSealApi: TraceSealApi = {
  async getLatestRun(): Promise<DashboardRunExport> {
    await delay(null);
    if (simulateError) throw new Error('Mock: failed to get latest run');
    return deleteRun;
  },

  async listRuns(): Promise<RunSummary[]> {
    await delay(null);
    if (simulateError) throw new Error('Mock: failed to list runs');
    if (simulateEmpty) return [];
    return runSummaries;
  },

  async getRun(runId: string): Promise<DashboardRunExport> {
    await delay(null);
    if (simulateError) throw new Error('Mock: failed to get run');
    const run = allRuns[runId];
    if (!run) throw new Error(`Mock: run not found: ${runId}`);
    return run;
  },

  async getPolicy(): Promise<PolicyRule[]> {
    await delay(null);
    if (simulateError) throw new Error('Mock: failed to get policy');
    return policyRules;
  },

  async getRuntimeInfo(): Promise<RuntimeInfo> {
    await delay(null);
    return runtimeInfo;
  },
};