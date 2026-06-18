import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { getTraceSealApi } from '../api';
import type { WorkspaceInfo } from '../api';
import { isElectronEnv } from '../utils/safety';

type WorkspaceStatus = 'loading' | 'ready' | 'error';

interface WorkspaceContextValue {
  workspace: WorkspaceInfo;
  status: WorkspaceStatus;
  error: Error | null;
  busy: boolean;
  revision: number;
  isLive: boolean;
  selectWorkspace(): Promise<WorkspaceInfo>;
  clearWorkspace(): Promise<void>;
  reloadWorkspace(): Promise<void>;
}

const EMPTY_WORKSPACE: WorkspaceInfo = {
  path: null,
  valid: false,
  hasRuns: false,
  hasPolicy: false,
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const api = useMemo(() => getTraceSealApi(), []);
  const isLive = isElectronEnv();
  const [workspace, setWorkspace] = useState<WorkspaceInfo>(EMPTY_WORKSPACE);
  const [status, setStatus] = useState<WorkspaceStatus>('loading');
  const [error, setError] = useState<Error | null>(null);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);

  const reloadWorkspace = useCallback(async () => {
    setStatus('loading');
    setError(null);
    try {
      const info = await api.getWorkspace();
      setWorkspace(info);
      setStatus('ready');
    } catch (reason) {
      setError(reason instanceof Error ? reason : new Error(String(reason)));
      setStatus('error');
    }
  }, [api]);

  useEffect(() => {
    void reloadWorkspace();
  }, [reloadWorkspace]);

  const selectWorkspace = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const previousPath = workspace.path;
      const info = await api.selectWorkspace();
      setWorkspace(info);
      setStatus('ready');
      if (info.valid && info.path && info.path !== previousPath) {
        setRevision((value) => value + 1);
      }
      return info;
    } catch (reason) {
      const nextError = reason instanceof Error ? reason : new Error(String(reason));
      setError(nextError);
      setStatus('error');
      throw nextError;
    } finally {
      setBusy(false);
    }
  }, [api, workspace.path]);

  const clearWorkspace = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      await api.clearWorkspace();
      setWorkspace(EMPTY_WORKSPACE);
      setStatus('ready');
      setRevision((value) => value + 1);
    } catch (reason) {
      const nextError = reason instanceof Error ? reason : new Error(String(reason));
      setError(nextError);
      setStatus('error');
      throw nextError;
    } finally {
      setBusy(false);
    }
  }, [api]);

  const value = useMemo<WorkspaceContextValue>(() => ({
    workspace,
    status,
    error,
    busy,
    revision,
    isLive,
    selectWorkspace,
    clearWorkspace,
    reloadWorkspace,
  }), [workspace, status, error, busy, revision, isLive, selectWorkspace, clearWorkspace, reloadWorkspace]);

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

const FALLBACK_WORKSPACE: WorkspaceInfo = {
  path: 'Unmanaged Workspace',
  valid: true,
  hasRuns: true,
  hasPolicy: true,
};

export function useWorkspace(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (context) return context;
  return {
    workspace: FALLBACK_WORKSPACE,
    status: 'ready',
    error: null,
    busy: false,
    revision: 0,
    isLive: isElectronEnv(),
    async selectWorkspace() { return FALLBACK_WORKSPACE; },
    async clearWorkspace() {},
    async reloadWorkspace() {},
  };
}
