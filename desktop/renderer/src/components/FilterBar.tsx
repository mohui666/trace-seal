import type { RiskLevel, RunStatus } from '../api';

interface FilterBarProps {
  search: string;
  onSearchChange: (v: string) => void;
  statusFilter?: RunStatus | 'all';
  onStatusFilterChange?: (v: RunStatus | 'all') => void;
  riskFilter?: RiskLevel | 'all';
  onRiskFilterChange?: (v: RiskLevel | 'all') => void;
  highRiskOnly?: boolean;
  onHighRiskOnlyChange?: (v: boolean) => void;
  onClear?: () => void;
}

export function FilterBar({
  search,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  riskFilter,
  onRiskFilterChange,
  highRiskOnly,
  onHighRiskOnlyChange,
  onClear,
}: FilterBarProps) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* Search */}
      <div className="relative">
        <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="搜索 Run ID 或命令..."
          className="pl-8 pr-3 py-1.5 text-xs bg-gray-900 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 w-56"
          aria-label="搜索运行"
        />
      </div>

      {/* Status filter */}
      {onStatusFilterChange && (
        <select
          value={statusFilter ?? 'all'}
          onChange={(e) => onStatusFilterChange(e.target.value as RunStatus | 'all')}
          className="px-2 py-1.5 text-xs bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:border-emerald-500"
          aria-label="状态筛选"
        >
          <option value="all">所有状态</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
          <option value="blocked">已阻断</option>
          <option value="running">运行中</option>
        </select>
      )}

      {/* Risk filter */}
      {onRiskFilterChange && (
        <select
          value={riskFilter ?? 'all'}
          onChange={(e) => onRiskFilterChange(e.target.value as RiskLevel | 'all')}
          className="px-2 py-1.5 text-xs bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:border-emerald-500"
          aria-label="风险等级筛选"
        >
          <option value="all">所有风险</option>
          <option value="low">低</option>
          <option value="medium">中</option>
          <option value="high">高</option>
          <option value="critical">严重</option>
        </select>
      )}

      {/* High risk only toggle */}
      {onHighRiskOnlyChange && (
        <label className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={highRiskOnly ?? false}
            onChange={(e) => onHighRiskOnlyChange(e.target.checked)}
            className="rounded border-gray-600 bg-gray-800 text-emerald-500 focus:ring-emerald-500"
          />
          仅高风险
        </label>
      )}

      {/* Clear */}
      {onClear && (
        <button
          onClick={onClear}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors focus:outline-none focus:underline"
        >
          清除筛选
        </button>
      )}
    </div>
  );
}