import type { RiskLevel } from '../api';

const riskConfig: Record<RiskLevel, { label: string; bg: string; text: string; border: string }> = {
  low: { label: '低', bg: 'bg-green-900/30', text: 'text-green-400', border: 'border-green-800' },
  medium: { label: '中', bg: 'bg-yellow-900/30', text: 'text-yellow-400', border: 'border-yellow-800' },
  high: { label: '高', bg: 'bg-orange-900/30', text: 'text-orange-400', border: 'border-orange-800' },
  critical: { label: '严重', bg: 'bg-red-900/30', text: 'text-red-400', border: 'border-red-800' },
};

export function RiskBadge({ level, className = '' }: { level?: RiskLevel; className?: string }) {
  if (!level) return null;
  const cfg = riskConfig[level];
  if (!cfg) return <span className="text-xs text-gray-500">{level}</span>;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${cfg.bg} ${cfg.text} ${cfg.border} ${className}`}
      role="status"
      aria-label={`风险等级: ${cfg.label}`}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'currentColor' }} aria-hidden="true" />
      {cfg.label}
    </span>
  );
}