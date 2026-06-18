import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { getTraceSealApi } from '../api/getTraceSealApi';
import { mockTraceSealApi as mockApiReference } from '../api/mockTraceSealApi';
import { AppShell } from '../layouts/AppShell';
import { HomePage } from '../pages/HomePage';
import { RunsPage } from '../pages/RunsPage';
import { RunDetailPage } from '../pages/RunDetailPage';
import { ExplainPage } from '../pages/ExplainPage';
import { PolicyPage } from '../pages/PolicyPage';
import type { TraceSealApi, DashboardRunExport, RunSummary, PolicyRule, TraceEvent } from '../api/contracts';

// ─── Test stubs ──────────────────────────────────────────────

function stubRun(overrides: Partial<DashboardRunExport> = {}): DashboardRunExport {
  return {
    schema_version: 1,
    run_id: 'test-run-001',
    command: 'traceseal run python test.py',
    started_at: '2026-06-17T10:00:00Z',
    finished_at: '2026-06-17T10:00:10Z',
    status: 'completed',
    exit_code: 0,
    event_count: 3,
    high_risk_count: 0,
    first_harmful_event: null,
    events: [],
    affected_files: [],
    suggested_policy: null,
    ...overrides,
  };
}

function stubEvent(overrides: Partial<TraceEvent> = {}): TraceEvent {
  return {
    id: 'evt_0001',
    type: 'shell',
    seq: 1,
    ts: '2026-06-17T10:00:00Z',
    ...overrides,
  };
}

function stubSummary(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: 'test-run-001',
    command: 'traceseal run python test.py',
    started_at: '2026-06-17T10:00:00Z',
    status: 'completed',
    event_count: 3,
    high_risk_count: 0,
    ...overrides,
  };
}

function stubPolicy(overrides: Partial<PolicyRule> = {}): PolicyRule {
  return {
    rule_id: 'test_rule',
    event_type: 'shell',
    pattern: '*',
    risk_level: 'high',
    action: 'warn',
    description: 'Test rule',
    ...overrides,
  };
}

function createMockApi(): TraceSealApi {
  return {
    getLatestRun: vi.fn(),
    listRuns: vi.fn(),
    getRun: vi.fn(),
    getPolicy: vi.fn(),
    getRuntimeInfo: vi.fn(),
  };
}

function installMockApi(mock: TraceSealApi) {
  (window as any).traceSeal = mock;
}

function uninstallMockApi() {
  delete (window as any).traceSeal;
}

// ─── Tests ───────────────────────────────────────────────────

describe('Renderer integration', () => {
  let mockApi: TraceSealApi;

  beforeEach(() => {
    mockApi = createMockApi();
    installMockApi(mockApi);
  });

  afterEach(() => {
    uninstallMockApi();
    vi.restoreAllMocks();
  });

  // ─── API priority ──────────────────────────────────────────

  describe('API priority', () => {
    it('uses real Electron API when window.traceSeal is set', () => {
      const api = getTraceSealApi();
      expect(api).toBe(mockApi);
    });

    it('falls back to mock API when window.traceSeal is not set', () => {
      uninstallMockApi();
      const api = getTraceSealApi();
      expect(api).toBe(mockApiReference);
    });
  });

  // ─── Home page ─────────────────────────────────────────────

  describe('HomePage', () => {
    it('shows loading state initially', async () => {
      (mockApi.getLatestRun as any).mockReturnValue(new Promise(() => {}));
      (mockApi.listRuns as any).mockReturnValue(new Promise(() => {}));

      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );

      expect(screen.getByText('加载仪表盘...')).toBeInTheDocument();
    });

    it('shows dashboard with real data', async () => {
      (mockApi.getLatestRun as any).mockResolvedValue(stubRun({ run_id: 'run-abc', event_count: 5, high_risk_count: 2 }));
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'run-abc', event_count: 5, high_risk_count: 2 }),
        stubSummary({ run_id: 'run-xyz', event_count: 3, high_risk_count: 0 }),
      ]);

      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
      });
    });

    it('shows first harmful event in latest run', async () => {
      const harmfulEvent = stubEvent({
        id: 'evt_bad',
        type: 'shell',
        operation: 'rm -rf /',
        risk: { level: 'critical', reasons: ['dangerous'], policy_rule: 'dangerous_delete', action: 'warn' },
      });

      (mockApi.getLatestRun as any).mockResolvedValue(
        stubRun({ run_id: 'run-abc', first_harmful_event: harmfulEvent, high_risk_count: 1 })
      );
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'run-abc', high_risk_count: 1, first_harmful_event_id: 'evt_bad' }),
      ]);

      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('First Harmful:')).toBeInTheDocument();
      });
    });

    it('shows "no harmful event" when first_harmful_event is null', async () => {
      (mockApi.getLatestRun as any).mockResolvedValue(stubRun({ first_harmful_event: null }));
      (mockApi.listRuns as any).mockResolvedValue([stubSummary()]);

      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('无有害事件')).toBeInTheDocument();
      });
    });

    it('shows error state with retry button', async () => {
      (mockApi.getLatestRun as any).mockRejectedValue(new Error('API error'));
      (mockApi.listRuns as any).mockRejectedValue(new Error('API error'));

      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('加载失败')).toBeInTheDocument();
        expect(screen.getByText('重试')).toBeInTheDocument();
      });
    });

    it('shows empty state when no runs', async () => {
      (mockApi.getLatestRun as any).mockResolvedValue(stubRun());
      (mockApi.listRuns as any).mockResolvedValue([]);

      render(
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('暂无运行记录')).toBeInTheDocument();
      });
    });
  });

  // ─── Runs page ─────────────────────────────────────────────

  describe('RunsPage', () => {
    it('shows runs table with data', async () => {
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'run-1', command: 'python test1.py', status: 'completed' }),
        stubSummary({ run_id: 'run-2', command: 'python test2.py', status: 'failed', exit_code: 1 }),
      ]);

      render(
        <MemoryRouter>
          <RunsPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('run-1')).toBeInTheDocument();
        expect(screen.getByText('run-2')).toBeInTheDocument();
      });
    });

    it('filters by search', async () => {
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'alpha', command: 'task A' }),
        stubSummary({ run_id: 'beta', command: 'task B' }),
      ]);

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <RunsPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('alpha')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('搜索 Run ID 或命令...');
      await user.type(searchInput, 'alpha');

      await waitFor(() => {
        expect(screen.getByText('alpha')).toBeInTheDocument();
        expect(screen.queryByText('beta')).not.toBeInTheDocument();
      });
    });

    it('filters by status', async () => {
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'run-ok', status: 'completed' }),
        stubSummary({ run_id: 'run-fail', status: 'failed', exit_code: 1 }),
      ]);

      render(
        <MemoryRouter>
          <RunsPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('run-ok')).toBeInTheDocument();
      });

      const statusSelect = screen.getByLabelText('状态筛选');
      fireEvent.change(statusSelect, { target: { value: 'failed' } });

      await waitFor(() => {
        expect(screen.queryByText('run-ok')).not.toBeInTheDocument();
        expect(screen.getByText('run-fail')).toBeInTheDocument();
      });
    });

    it('filters by high risk only', async () => {
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'run-safe', high_risk_count: 0 }),
        stubSummary({ run_id: 'run-risk', high_risk_count: 3, first_harmful_event_id: 'evt_x' }),
      ]);

      render(
        <MemoryRouter>
          <RunsPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('run-safe')).toBeInTheDocument();
      });

      const checkbox = screen.getByText('仅高风险');
      fireEvent.click(checkbox);

      await waitFor(() => {
        expect(screen.queryByText('run-safe')).not.toBeInTheDocument();
        expect(screen.getByText('run-risk')).toBeInTheDocument();
      });
    });

    it('shows empty state when no results match filter', async () => {
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'run-1', command: 'task A' }),
      ]);

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <RunsPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('run-1')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('搜索 Run ID 或命令...');
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText('暂无运行记录')).toBeInTheDocument();
      });
    });

    it('handles long command without breaking layout', async () => {
      const longCmd = 'traceseal run python examples/bad_agent_delete.py --very-long-argument --another-flag --verbose --debug --trace --output-dir=./logs --config=./config.json';
      (mockApi.listRuns as any).mockResolvedValue([
        stubSummary({ run_id: 'run-long', command: longCmd }),
      ]);

      render(
        <MemoryRouter>
          <RunsPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        const cmdCell = screen.getByText(/traceseal run python examples\/bad_agent_delete\.py/);
        expect(cmdCell).toBeInTheDocument();
        const td = cmdCell.closest('td');
        expect(td?.getAttribute('title')).toBe(longCmd);
      });
    });
  });

  // ─── Run Detail page ───────────────────────────────────────

  describe('RunDetailPage', () => {
    it('shows run details', async () => {
      const harmfulEvent = stubEvent({
        id: 'evt_bad',
        type: 'shell',
        operation: 'rm -rf /',
        risk: { level: 'critical', reasons: ['dangerous'], policy_rule: 'dangerous_delete' },
      });

      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-detail-1',
          command: 'python test.py',
          event_count: 4,
          high_risk_count: 1,
          first_harmful_event: harmfulEvent,
          events: [
            stubEvent({ id: 'evt_1', type: 'file.write', input: { path: '/tmp/test.txt' } }),
            stubEvent({ id: 'evt_2', type: 'shell', input: { command: 'ls' }, output: { status: 'ok' } }),
            harmfulEvent,
            stubEvent({ id: 'evt_3', type: 'http', input: { method: 'GET', url: 'https://api.example.com' } }),
          ],
        })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-detail-1']}>
          <Routes>
            <Route path="/runs/:id" element={<RunDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      const heading = await screen.findByText('Run Detail', {}, { timeout: 3000 });
      expect(heading).toBeInTheDocument();
      const runIdElements = screen.getAllByText('run-detail-1');
      expect(runIdElements.length).toBeGreaterThan(0);
    });

    it('handles missing optional fields', async () => {
      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-minimal',
          command: 'python test.py',
          started_at: undefined,
          finished_at: undefined,
          exit_code: undefined,
          status: undefined,
          first_harmful_event: null,
          events: [],
        })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-minimal']}>
          <Routes>
            <Route path="/runs/:id" element={<RunDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Run Detail')).toBeInTheDocument();
        const runIdElements = screen.getAllByText('run-minimal');
        expect(runIdElements.length).toBeGreaterThan(0);
        // Should not crash - should show "-" for missing dates
        expect(screen.getAllByText('-').length).toBeGreaterThan(0);
      });
    });

    it('shows unknown event type without crashing', async () => {
      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-unknown-type',
          events: [
            stubEvent({
              id: 'evt_unknown',
              type: 'custom.action',
              operation: 'do_something',
              input: { key: 'value' },
            }),
          ],
        })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-unknown-type']}>
          <Routes>
            <Route path="/runs/:id" element={<RunDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('custom.action')).toBeInTheDocument();
      });

      // Expand event
      const eventButton = screen.getByText('custom.action').closest('button');
      fireEvent.click(eventButton!);

      await waitFor(() => {
        expect(screen.getByText('通用事件详情')).toBeInTheDocument();
      });
    });

    it('shows empty events message', async () => {
      (mockApi.getRun as any).mockResolvedValue(
        stubRun({ run_id: 'run-empty-events', events: [] })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-empty-events']}>
          <Routes>
            <Route path="/runs/:id" element={<RunDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('无事件记录')).toBeInTheDocument();
      });
    });

    it('handles SDK event type', async () => {
      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-sdk',
          events: [
            stubEvent({
              id: 'evt_sdk',
              type: 'sdk',
              operation: 'sdk.hook',
              output: { status: 'ok' },
            }),
          ],
        })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-sdk']}>
          <Routes>
            <Route path="/runs/:id" element={<RunDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('sdk')).toBeInTheDocument();
      });

      const eventButton = screen.getByText('sdk').closest('button');
      fireEvent.click(eventButton!);

      await waitFor(() => {
        expect(screen.getByText('SDK')).toBeInTheDocument();
      });
    });
  });

  // ─── Explain page ──────────────────────────────────────────

  describe('ExplainPage', () => {
    it('shows no harmful event message', async () => {
      (mockApi.getRun as any).mockResolvedValue(
        stubRun({ run_id: 'run-clean', first_harmful_event: null })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-clean/explain']}>
          <Routes>
            <Route path="/runs/:id/explain" element={<ExplainPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('未发现有害调用')).toBeInTheDocument();
      });
    });

    it('shows harmful event analysis', async () => {
      const harmfulEvent = stubEvent({
        id: 'evt_bad',
        type: 'shell',
        operation: 'rm -rf /',
        risk: {
          level: 'critical',
          reasons: ['recursive force delete', 'deleted protected path'],
          policy_rule: 'dangerous_delete',
          action: 'warn',
        },
      });

      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-bad',
          first_harmful_event: harmfulEvent,
          affected_files: ['/tmp/test.txt', '/tmp/data'],
          suggested_policy: 'deny shell "rm -rf /**"',
        })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-bad/explain']}>
          <Routes>
            <Route path="/runs/:id/explain" element={<ExplainPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('First Harmful Tool Call')).toBeInTheDocument();
        expect(screen.getByText('recursive force delete')).toBeInTheDocument();
        expect(screen.getByText('/tmp/test.txt')).toBeInTheDocument();
        expect(screen.getByText('deny shell "rm -rf /**"')).toBeInTheDocument();
      });
    });

    it('handles empty suggested_policy', async () => {
      const harmfulEvent = stubEvent({
        id: 'evt_bad',
        type: 'shell',
        risk: { level: 'high', reasons: ['test'] },
      });

      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-no-policy',
          first_harmful_event: harmfulEvent,
          suggested_policy: null,
        })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-no-policy/explain']}>
          <Routes>
            <Route path="/runs/:id/explain" element={<ExplainPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('First Harmful Tool Call')).toBeInTheDocument();
        expect(screen.queryByText('Suggested Policy')).not.toBeInTheDocument();
      });
    });

    it('handles empty affected_files', async () => {
      const harmfulEvent = stubEvent({
        id: 'evt_bad',
        type: 'shell',
        risk: { level: 'high', reasons: ['test'] },
      });

      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-no-files',
          first_harmful_event: harmfulEvent,
          affected_files: [],
        })
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-no-files/explain']}>
          <Routes>
            <Route path="/runs/:id/explain" element={<ExplainPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('First Harmful Tool Call')).toBeInTheDocument();
        expect(screen.queryByText('Affected Files')).not.toBeInTheDocument();
      });
    });
  });

  // ─── Policy page ───────────────────────────────────────────

  describe('PolicyPage', () => {
    it('shows policy rules', async () => {
      (mockApi.getPolicy as any).mockResolvedValue([
        stubPolicy({ rule_id: 'rule_1', description: 'First rule' }),
        stubPolicy({ rule_id: 'rule_2', description: 'Second rule', risk_level: 'critical' }),
      ]);

      render(
        <MemoryRouter>
          <PolicyPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('rule_1')).toBeInTheDocument();
        expect(screen.getByText('rule_2')).toBeInTheDocument();
      });
    });

    it('shows error state with retry', async () => {
      (mockApi.getPolicy as any).mockRejectedValue(new Error('Failed to load policy'));

      render(
        <MemoryRouter>
          <PolicyPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Failed to load policy')).toBeInTheDocument();
        expect(screen.getByText('重试')).toBeInTheDocument();
      });
    });

    it('filters by risk level', async () => {
      (mockApi.getPolicy as any).mockResolvedValue([
        stubPolicy({ rule_id: 'low_rule', risk_level: 'low' }),
        stubPolicy({ rule_id: 'high_rule', risk_level: 'high' }),
      ]);

      render(
        <MemoryRouter>
          <PolicyPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('low_rule')).toBeInTheDocument();
      });

      const riskSelect = screen.getByLabelText('风险等级筛选');
      fireEvent.change(riskSelect, { target: { value: 'high' } });

      await waitFor(() => {
        expect(screen.queryByText('low_rule')).not.toBeInTheDocument();
        expect(screen.getByText('high_rule')).toBeInTheDocument();
      });
    });
  });

  // ─── Live/Mock indicator ───────────────────────────────────

  describe('Live/Mock indicator', () => {
    it('shows Live Electron when window.traceSeal is set', () => {
      render(
        <MemoryRouter>
          <AppShell>
            <div data-testid="content">content</div>
          </AppShell>
        </MemoryRouter>
      );

      expect(screen.getByText('Live Electron')).toBeInTheDocument();
    });

    it('shows Mock Data when window.traceSeal is not set', () => {
      uninstallMockApi();

      render(
        <MemoryRouter>
          <AppShell>
            <div data-testid="content">content</div>
          </AppShell>
        </MemoryRouter>
      );

      expect(screen.getByText('Mock Data')).toBeInTheDocument();
    });
  });

  // ─── HashRouter navigation ─────────────────────────────────

  describe('HashRouter', () => {
    it('renders home page at /', async () => {
      (mockApi.getLatestRun as any).mockResolvedValue(stubRun());
      (mockApi.listRuns as any).mockResolvedValue([stubSummary()]);

      render(
        <MemoryRouter initialEntries={['/']}>
          <HomePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
      });
    });

    it('renders runs page at /runs', async () => {
      (mockApi.listRuns as any).mockResolvedValue([stubSummary()]);

      render(
        <MemoryRouter initialEntries={['/runs']}>
          <Routes>
            <Route path="/runs" element={<RunsPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Runs')).toBeInTheDocument();
      });
    });

    it('renders policy page at /policy', async () => {
      (mockApi.getPolicy as any).mockResolvedValue([stubPolicy()]);

      render(
        <MemoryRouter initialEntries={['/policy']}>
          <Routes>
            <Route path="/policy" element={<PolicyPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Policy')).toBeInTheDocument();
      });
    });
  });

  // ─── CopyButton failure ────────────────────────────────────

  describe('CopyButton', () => {
    it('shows failed state when clipboard API fails', async () => {
      const harmfulEvent = stubEvent({
        id: 'evt_bad',
        type: 'shell',
        operation: 'rm -rf /',
        risk: { level: 'critical', reasons: ['test'] },
      });

      (mockApi.getRun as any).mockResolvedValue(
        stubRun({
          run_id: 'run-copy',
          first_harmful_event: harmfulEvent,
          suggested_policy: 'deny shell "rm -rf /**"',
        })
      );

      // Mock clipboard API to fail
      const writeTextMock = vi.fn().mockRejectedValue(new Error('Clipboard denied'));
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: writeTextMock },
        configurable: true,
      });

      render(
        <MemoryRouter initialEntries={['/runs/run-copy/explain']}>
          <Routes>
            <Route path="/runs/:id/explain" element={<ExplainPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('复制规则')).toBeInTheDocument();
      });

      const copyBtn = screen.getByText('复制规则');
      fireEvent.click(copyBtn);

      await waitFor(() => {
        expect(screen.getByText('复制失败')).toBeInTheDocument();
      });
    });
  });
});