import { useState, useMemo } from 'react';
import { useAsync } from '../hooks/useAsync';
import { getTraceSealApi } from '../api';
import { PolicyList, FilterBar, LoadingState, ErrorState, PageHeader } from '../components';
import type { RiskLevel, PolicyAction } from '../api';

export function PolicyPage() {
  const api = useMemo(() => getTraceSealApi(), []);
  const { status, data: rules, error, refetch } = useAsync(() => api.getPolicy(), [api]);

  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<RiskLevel | 'all'>('all');
  const [actionFilter, setActionFilter] = useState<PolicyAction | 'all'>('all');

  const filtered = useMemo(() => {
    if (!rules) return [];
    return rules.filter((r) => {
      if (search) {
        const q = search.toLowerCase();
        if (!r.rule_id.toLowerCase().includes(q) && !r.description?.toLowerCase().includes(q)) return false;
      }
      if (riskFilter !== 'all' && r.risk_level !== riskFilter) return false;
      if (actionFilter !== 'all' && r.action !== actionFilter) return false;
      return true;
    });
  }, [rules, search, riskFilter, actionFilter]);

  if (status === 'loading') return <LoadingState message="加载策略..." />;
  if (status === 'error') return <ErrorState message={error.message} onRetry={refetch} />;

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Policy" description="安全策略规则（只读）" />
      <div className="p-6 space-y-4">
        <FilterBar
          search={search}
          onSearchChange={setSearch}
          riskFilter={riskFilter}
          onRiskFilterChange={setRiskFilter}
          onClear={() => { setSearch(''); setRiskFilter('all'); setActionFilter('all'); }}
        />
        <div className="flex items-center gap-2">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value as PolicyAction | 'all')}
            className="px-2 py-1.5 text-xs bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:border-emerald-500"
            aria-label="动作筛选"
          >
            <option value="all">所有动作</option>
            <option value="warn">warn</option>
            <option value="deny">deny</option>
            <option value="block">block</option>
            <option value="require_approval">require_approval</option>
          </select>
        </div>
        <PolicyList rules={filtered} />
      </div>
    </div>
  );
}