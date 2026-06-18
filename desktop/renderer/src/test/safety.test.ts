import { describe, it, expect } from 'vitest';
import {
  formatDate,
  formatTime,
  formatCommand,
  getEventPrimaryInput,
  getEventOutputStatus,
  normalizeRiskLevel,
  normalizeRunStatus,
  safeGet,
  isElectronEnv,
} from '../utils/safety';
import type { TraceEvent } from '../api/contracts';

describe('safety utilities', () => {
  describe('formatDate', () => {
    it('returns "-" for undefined', () => {
      expect(formatDate(undefined)).toBe('-');
    });

    it('returns "-" for null', () => {
      expect(formatDate(null)).toBe('-');
    });

    it('returns "-" for empty string', () => {
      expect(formatDate('')).toBe('-');
    });

    it('formats valid ISO date', () => {
      const result = formatDate('2026-06-17T10:00:00Z');
      expect(result).toContain('2026');
      expect(result).toContain('06');
      expect(result).toContain('17');
    });

    it('returns original string for invalid date', () => {
      expect(formatDate('not-a-date')).toBe('not-a-date');
    });
  });

  describe('formatTime', () => {
    it('returns "-" for undefined', () => {
      expect(formatTime(undefined)).toBe('-');
    });

    it('extracts time from ISO string', () => {
      const result = formatTime('2026-06-17T10:30:45Z');
      // toLocaleTimeString may convert to local timezone, so just check it's a time string
      expect(result).toMatch(/\d{2}:\d{2}:\d{2}/);
    });

    it('handles date-only string', () => {
      const result = formatTime('2026-06-17');
      // Should not throw
      expect(typeof result).toBe('string');
    });
  });

  describe('formatCommand', () => {
    it('returns empty string for empty command', () => {
      expect(formatCommand('')).toBe('');
    });

    it('returns short command as-is', () => {
      const cmd = 'python -m pytest';
      expect(formatCommand(cmd)).toBe(cmd);
    });

    it('truncates long command', () => {
      const cmd = 'traceseal run python examples/bad_agent_delete.py --very-long-argument --another-long-flag --verbose --debug --trace';
      const result = formatCommand(cmd, 50);
      expect(result.length).toBeLessThanOrEqual(53); // 50 + "..."
      expect(result.endsWith('...')).toBe(true);
    });
  });

  describe('getEventPrimaryInput', () => {
    it('extracts path for file events', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'file.write',
        input: { path: '/tmp/test.txt' },
      };
      expect(getEventPrimaryInput(event as TraceEvent)).toBe('/tmp/test.txt');
    });

    it('extracts command for shell events', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'shell',
        input: { command: 'rm -rf /tmp' },
      };
      expect(getEventPrimaryInput(event as TraceEvent)).toBe('rm -rf /tmp');
    });

    it('extracts URL for HTTP events', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'http',
        input: { method: 'POST', url: 'https://example.com/api' },
      };
      expect(getEventPrimaryInput(event as TraceEvent)).toBe('POST https://example.com/api');
    });

    it('falls back to operation when no input', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'sdk',
        operation: 'sdk.call',
        input: {},
      };
      expect(getEventPrimaryInput(event as TraceEvent)).toBe('sdk.call');
    });

    it('falls back to type when no operation or input', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'unknown',
      };
      expect(getEventPrimaryInput(event as TraceEvent)).toBe('unknown');
    });
  });

  describe('getEventOutputStatus', () => {
    it('returns null for missing output', () => {
      const event: Partial<TraceEvent> = { id: 'evt_1', type: 'shell' };
      expect(getEventOutputStatus(event as TraceEvent)).toBeNull();
    });

    it('returns status string', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'shell',
        output: { status: 'ok' },
      };
      expect(getEventOutputStatus(event as TraceEvent)).toBe('ok');
    });

    it('infers ok from returncode 0', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'shell',
        output: { returncode: 0 },
      };
      expect(getEventOutputStatus(event as TraceEvent)).toBe('ok');
    });

    it('infers failed from non-zero returncode', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'shell',
        output: { returncode: 1 },
      };
      expect(getEventOutputStatus(event as TraceEvent)).toBe('failed');
    });

    it('infers ok from HTTP status_code < 400', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'http',
        output: { status_code: 200 },
      };
      expect(getEventOutputStatus(event as TraceEvent)).toBe('ok');
    });

    it('infers failed from HTTP status_code >= 400', () => {
      const event: Partial<TraceEvent> = {
        id: 'evt_1',
        type: 'http',
        output: { status_code: 500 },
      };
      expect(getEventOutputStatus(event as TraceEvent)).toBe('failed');
    });
  });

  describe('normalizeRiskLevel', () => {
    it('returns undefined for null', () => {
      expect(normalizeRiskLevel(null)).toBeUndefined();
    });

    it('returns undefined for empty string', () => {
      expect(normalizeRiskLevel('')).toBeUndefined();
    });

    it('returns valid level', () => {
      expect(normalizeRiskLevel('critical')).toBe('critical');
      expect(normalizeRiskLevel('high')).toBe('high');
      expect(normalizeRiskLevel('medium')).toBe('medium');
      expect(normalizeRiskLevel('low')).toBe('low');
    });

    it('returns undefined for invalid level', () => {
      expect(normalizeRiskLevel('unknown')).toBeUndefined();
      expect(normalizeRiskLevel('extra-high')).toBeUndefined();
    });
  });

  describe('normalizeRunStatus', () => {
    it('returns undefined for null', () => {
      expect(normalizeRunStatus(null)).toBeUndefined();
    });

    it('returns valid status', () => {
      expect(normalizeRunStatus('completed')).toBe('completed');
      expect(normalizeRunStatus('failed')).toBe('failed');
      expect(normalizeRunStatus('blocked')).toBe('blocked');
      expect(normalizeRunStatus('running')).toBe('running');
    });

    it('returns undefined for unknown status', () => {
      expect(normalizeRunStatus('unknown')).toBeUndefined();
      expect(normalizeRunStatus('crashed')).toBeUndefined();
    });
  });

  describe('safeGet', () => {
    it('returns nested value', () => {
      const obj = { a: { b: { c: 42 } } };
      expect(safeGet(obj, ['a', 'b', 'c'])).toBe(42);
    });

    it('returns undefined for missing path', () => {
      const obj = { a: { b: {} } };
      expect(safeGet(obj, ['a', 'b', 'c'])).toBeUndefined();
    });

    it('returns default value for missing path', () => {
      const obj = { a: { b: {} } };
      expect(safeGet(obj, ['a', 'b', 'c'], 'default')).toBe('default');
    });

    it('returns undefined for null object', () => {
      expect(safeGet(null, ['a', 'b'])).toBeUndefined();
    });
  });

  describe('isElectronEnv', () => {
    it('returns false when window.traceSeal is not set', () => {
      delete (window as any).traceSeal;
      expect(isElectronEnv()).toBe(false);
    });

    it('returns true when window.traceSeal is set', () => {
      (window as any).traceSeal = {};
      expect(isElectronEnv()).toBe(true);
      delete (window as any).traceSeal;
    });
  });
});