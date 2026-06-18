import type { TraceEvent, RiskLevel, RunStatus } from '../api/contracts';

/**
 * 安全格式化日期字符串。
 * 输入可能为 undefined、null、空字符串或非标准格式。
 */
export function formatDate(dateStr: string | undefined | null): string {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr; // 返回原始字符串，不报错
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * 安全格式化日期（仅显示时间）。
 */
export function formatTime(dateStr: string | undefined | null): string {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr.slice(11, 19) || dateStr;
    return d.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * 安全格式化命令字符串。
 * 超长命令会被截断并添加省略号提示。
 */
export function formatCommand(cmd: string, maxLen = 120): string {
  if (!cmd) return '';
  if (cmd.length <= maxLen) return cmd;
  return cmd.slice(0, maxLen) + '...';
}

/**
 * 获取事件的主要输入描述。
 * 不同事件类型有不同的 input 字段结构。
 */
export function getEventPrimaryInput(event: TraceEvent): string {
  if (!event) return 'unknown';

  const input = event.input;
  if (!input || typeof input !== 'object') return event.operation ?? event.type;

  // 按字段优先级提取
  const path = input.path;
  const command = input.command;
  const url = input.url;
  const method = input.method;

  if (typeof command === 'string') return command;
  if (typeof path === 'string') return path;
  if (typeof url === 'string') {
    const m = typeof method === 'string' ? method + ' ' : '';
    return m + url;
  }

  return event.operation ?? event.type;
}

/**
 * 获取事件输出状态字符串。
 * output 字段结构不固定，可能是 { status: "ok" } 或 { returncode: 0 } 等。
 */
export function getEventOutputStatus(event: TraceEvent): string | null {
  if (!event?.output || typeof event.output !== 'object') return null;

  const s = event.output.status;
  if (typeof s === 'string') return s;

  // 尝试从 returncode 推断
  const rc = event.output.returncode;
  if (typeof rc === 'number') {
    return rc === 0 ? 'ok' : 'failed';
  }

  // 尝试从 status_code 推断
  const sc = event.output.status_code;
  if (typeof sc === 'number') {
    return sc < 400 ? 'ok' : 'failed';
  }

  return null;
}

/**
 * 标准化风险等级。
 * 如果输入不是合法值，返回 'low' 作为默认值，不报错。
 */
export function normalizeRiskLevel(level: string | undefined | null): RiskLevel | undefined {
  if (!level) return undefined;
  const valid: RiskLevel[] = ['low', 'medium', 'high', 'critical'];
  if (valid.includes(level as RiskLevel)) return level as RiskLevel;
  return undefined;
}

/**
 * 标准化运行状态。
 * 如果输入不是合法值，返回 undefined，不报错。
 */
export function normalizeRunStatus(status: string | undefined | null): RunStatus | undefined {
  if (!status) return undefined;
  const valid: RunStatus[] = ['completed', 'failed', 'blocked', 'running'];
  if (valid.includes(status as RunStatus)) return status as RunStatus;
  return undefined;
}

/**
 * 安全获取嵌套属性。
 * 避免因中间属性为 null/undefined 导致 TypeError。
 */
export function safeGet<T = unknown>(
  obj: unknown,
  path: string[],
  defaultValue?: T
): T | undefined {
  let current: unknown = obj;
  for (const key of path) {
    if (current == null || typeof current !== 'object') return defaultValue;
    current = (current as Record<string, unknown>)[key];
  }
  return (current as T | undefined) ?? defaultValue;
}

/**
 * 判断当前是否运行在 Electron 环境（有真实 API）。
 */
export function isElectronEnv(): boolean {
  return Boolean(window.traceSeal);
}