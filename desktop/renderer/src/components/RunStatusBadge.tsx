import type { RunStatus } from '../api';

const statusConfig: Record<RunStatus, { label: string; bg: string; text: string }> = {
  completed: { label: '已完成', bg: 'bg-green-900/30', text: 'text-green-400' },
  failed: { label: '失败', bg: 'bg-red-900/30', text: 'text-red-400' },
  blocked: { label: '已阻断', bg: 'bg-yellow-900/30', text: 'text-yellow-400' },
  running: { label: '运行中', bg: 'bg-blue-900/30', text: 'text-blue-400' },
};

export function RunStatusBadge({ status, className = '' }: { status?: RunStatus; className?: string }) {
  if (!status) return null;
  const cfg = statusConfig[status];
  if (!cfg) return <span className="text-xs text-gray-500">{status}</span>;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${cfg.bg} ${cfg.text} ${className}`}
      role="status"
      aria-label={`状态: ${cfg.label}`}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'currentColor' }} aria-hidden="true" />
      {cfg.label}
    </span>
  );
}