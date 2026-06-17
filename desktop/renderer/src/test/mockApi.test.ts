import { describe, it, expect } from 'vitest';
import { mockTraceSealApi } from '../api/mockTraceSealApi';

describe('Mock API', () => {
  it('listRuns returns all summaries', async () => {
    const runs = await mockTraceSealApi.listRuns();
    expect(runs.length).toBe(7);
    expect(runs[0].run_id).toBe('run-delete-001');
  });

  it('getRun returns delete demo', async () => {
    const run = await mockTraceSealApi.getRun('run-delete-001');
    expect(run.run_id).toBe('run-delete-001');
    expect(run.events.length).toBe(4);
    expect(run.first_harmful_event).toBeDefined();
    expect(run.first_harmful_event?.risk?.level).toBe('critical');
  });

  it('getRun returns env demo', async () => {
    const run = await mockTraceSealApi.getRun('run-env-001');
    expect(run.high_risk_count).toBe(2);
    expect(run.first_harmful_event?.risk?.policy_rule).toBe('env_write');
  });

  it('getRun returns git demo', async () => {
    const run = await mockTraceSealApi.getRun('run-git-001');
    expect(run.first_harmful_event?.risk?.policy_rule).toBe('git_push');
  });

  it('getRun returns http demo', async () => {
    const run = await mockTraceSealApi.getRun('run-http-001');
    expect(run.high_risk_count).toBe(2);
  });

  it('getRun returns clean run with no harmful event', async () => {
    const run = await mockTraceSealApi.getRun('run-clean-001');
    expect(run.first_harmful_event).toBeNull();
    expect(run.high_risk_count).toBe(0);
  });

  it('getRun returns failed run', async () => {
    const run = await mockTraceSealApi.getRun('run-failed-001');
    expect(run.status).toBe('failed');
    expect(run.exit_code).toBe(1);
  });

  it('getRun returns blocked run', async () => {
    const run = await mockTraceSealApi.getRun('run-blocked-001');
    expect(run.status).toBe('blocked');
    expect(run.first_harmful_event?.risk?.action).toBe('block');
  });

  it('getRun throws for unknown run', async () => {
    await expect(mockTraceSealApi.getRun('unknown')).rejects.toThrow('run not found');
  });

  it('getPolicy returns 4 rules', async () => {
    const rules = await mockTraceSealApi.getPolicy();
    expect(rules.length).toBe(4);
    expect(rules[0].rule_id).toBe('dangerous_delete');
  });

  it('getLatestRun returns delete demo', async () => {
    const run = await mockTraceSealApi.getLatestRun();
    expect(run.run_id).toBe('run-delete-001');
  });

  it('getRuntimeInfo returns info', async () => {
    const info = await mockTraceSealApi.getRuntimeInfo();
    expect(info.platform).toBe('win32');
    expect(info.version).toBe('0.2.0-dev');
  });
});