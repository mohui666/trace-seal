import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { DashboardRunExport, TraceSealApi, WorkspaceInfo } from '../api';
import { AppShell } from '../layouts/AppShell';
import { HomePage } from '../pages/HomePage';
import { WorkspaceProvider } from '../workspace';

const EMPTY: WorkspaceInfo = { path: null, valid: false, hasRuns: false, hasPolicy: false };
const FIRST: WorkspaceInfo = { path: 'C:\\TraceSeal Workspace', valid: true, hasRuns: true, hasPolicy: true };
const SECOND: WorkspaceInfo = { path: 'C:\\中文 工作区', valid: true, hasRuns: true, hasPolicy: false };

const RUN: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-real-001',
  command: 'python agent.py',
  status: 'completed',
  exit_code: 0,
  event_count: 1,
  high_risk_count: 0,
  first_harmful_event: null,
  events: [],
  affected_files: [],
  suggested_policy: null,
};

function api(overrides: Partial<TraceSealApi> = {}): TraceSealApi {
  return {
    getLatestRun: vi.fn().mockResolvedValue(RUN),
    listRuns: vi.fn().mockResolvedValue([{
      run_id: RUN.run_id,
      command: RUN.command,
      status: RUN.status,
      exit_code: RUN.exit_code,
      event_count: RUN.event_count,
      high_risk_count: RUN.high_risk_count,
    }]),
    getRun: vi.fn().mockResolvedValue(RUN),
    getPolicy: vi.fn().mockResolvedValue([]),
    getRuntimeInfo: vi.fn().mockResolvedValue({ pythonCommand: 'bundled', repositoryRoot: FIRST.path!, platform: 'win32' }),
    selectWorkspace: vi.fn().mockResolvedValue(FIRST),
    getWorkspace: vi.fn().mockResolvedValue(FIRST),
    clearWorkspace: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

function renderShell(traceSealApi: TraceSealApi, child = <div data-testid="workspace-content">content</div>) {
  window.traceSeal = traceSealApi;
  return render(
    <MemoryRouter>
      <WorkspaceProvider>
        <AppShell>{child}</AppShell>
      </WorkspaceProvider>
    </MemoryRouter>,
  );
}

describe('workspace UX', () => {
  beforeEach(() => { vi.restoreAllMocks(); });
  afterEach(() => { delete window.traceSeal; });

  it('shows first-start guidance when no workspace is configured', async () => {
    renderShell(api({ getWorkspace: vi.fn().mockResolvedValue(EMPTY) }));
    expect(await screen.findByText('选择 TraceSeal 工作区')).toBeInTheDocument();
    expect(screen.queryByTestId('workspace-content')).not.toBeInTheDocument();
  });

  it('selects a workspace and reveals dashboard content', async () => {
    const traceSealApi = api({
      getWorkspace: vi.fn().mockResolvedValue(EMPTY),
      selectWorkspace: vi.fn().mockResolvedValue(FIRST),
    });
    renderShell(traceSealApi);
    await screen.findByText('选择 TraceSeal 工作区');
    fireEvent.click(screen.getAllByRole('button', { name: '选择工作区' })[0]);
    expect(await screen.findByTestId('workspace-content')).toBeInTheDocument();
    expect(traceSealApi.selectWorkspace).toHaveBeenCalledTimes(1);
    expect(screen.getByText(FIRST.path!)).toBeInTheDocument();
  });

  it('keeps first-start guidance when directory selection is cancelled', async () => {
    const traceSealApi = api({
      getWorkspace: vi.fn().mockResolvedValue(EMPTY),
      selectWorkspace: vi.fn().mockResolvedValue(EMPTY),
    });
    renderShell(traceSealApi);
    await screen.findByText('选择 TraceSeal 工作区');
    fireEvent.click(screen.getAllByRole('button', { name: '选择工作区' })[0]);
    await waitFor(() => expect(traceSealApi.selectWorkspace).toHaveBeenCalledTimes(1));
    expect(screen.getByText('选择 TraceSeal 工作区')).toBeInTheDocument();
  });

  it('shows an invalid workspace warning', async () => {
    renderShell(api({
      getWorkspace: vi.fn().mockResolvedValue({ path: 'C:\\missing', valid: false, hasRuns: false, hasPolicy: false }),
    }));
    expect(await screen.findByText('工作区无效')).toBeInTheDocument();
    expect(screen.getAllByText('C:\\missing').length).toBeGreaterThan(0);
  });

  it('clears a workspace and returns to first-start state', async () => {
    const traceSealApi = api();
    renderShell(traceSealApi);
    await screen.findByTestId('workspace-content');
    fireEvent.click(screen.getByRole('button', { name: '清除工作区' }));
    expect(await screen.findByText('选择 TraceSeal 工作区')).toBeInTheDocument();
    expect(traceSealApi.clearWorkspace).toHaveBeenCalledTimes(1);
  });

  it('reloads latest and runs after switching workspace without reloading the window', async () => {
    const traceSealApi = api({ selectWorkspace: vi.fn().mockResolvedValue(SECOND) });
    renderShell(traceSealApi, <HomePage />);
    expect((await screen.findAllByText('run-real-001')).length).toBeGreaterThan(0);
    expect(traceSealApi.listRuns).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', { name: '切换工作区' }));
    await waitFor(() => expect(traceSealApi.listRuns).toHaveBeenCalledTimes(2));
    expect(traceSealApi.getLatestRun).toHaveBeenCalledTimes(2);
    expect(screen.getByText(SECOND.path!)).toBeInTheDocument();
  });

  it('guides the user when the selected workspace has no runs', async () => {
    const traceSealApi = api({
      getWorkspace: vi.fn().mockResolvedValue({ ...FIRST, hasRuns: false }),
      listRuns: vi.fn().mockResolvedValue([]),
      getLatestRun: vi.fn().mockRejectedValue(new Error('RUN_NOT_FOUND')),
    });
    renderShell(traceSealApi, <HomePage />);
    expect((await screen.findAllByText('暂无运行记录')).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/当前工作区还没有 Runs/).length).toBeGreaterThan(0);
  });

  it('shows workspace API errors and supports retry', async () => {
    const getWorkspace = vi.fn()
      .mockRejectedValueOnce(new Error('settings unavailable'))
      .mockResolvedValueOnce(EMPTY);
    renderShell(api({ getWorkspace }));
    expect(await screen.findByText('工作区 API 出错')).toBeInTheDocument();
    expect(screen.getByText('settings unavailable')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '重试' }));
    expect(await screen.findByText('选择 TraceSeal 工作区')).toBeInTheDocument();
  });

  it('remains compatible with browser mock mode', async () => {
    delete window.traceSeal;
    render(
      <MemoryRouter>
        <WorkspaceProvider>
          <AppShell><div data-testid="mock-content">mock content</div></AppShell>
        </WorkspaceProvider>
      </MemoryRouter>,
    );
    expect(screen.getByText('Mock Data')).toBeInTheDocument();
    expect(await screen.findByTestId('mock-content')).toBeInTheDocument();
  });
});
