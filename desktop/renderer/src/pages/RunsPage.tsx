import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAsync } from '../hooks/useAsync';
import { getTraceSealApi } from '../api';
import { RunsTable, FilterBar, LoadingState, ErrorState, EmptyState, PageHeader } from '../components';
import type { RunStatus } from '../api';

export function RunsPage() {
  const api = useMemo(() => getTraceSealApi(), []);
  const { status, data: runs, error, refetch } = useAsync(() => api.listRuns(), [api]);
  const navigate = useNavigate();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<RunStatus | 'all'>('all');
  const [highRiskOnly, setHighRiskOnly] = useState(false);

  const filtered = useMemo(() => {
    if (!runs) return [];
    return runs.filter((r) => {
      if (search) {
        const q = search.toLowerCase();
        if (!r.run_id.toLowerCase().includes(q) && !r.command.toLowerCase().includes(q)) return false;
      }
      if (statusFilter !== 'all' && r.status !== statusFilter) return false;
      if (highRiskOnly && r.high_risk_count === 0) return false;
      return true;
    });
  }, [runs, search, statusFilter, highRiskOnly]);

  const clearFilters = () => {
    setSearch('');
    setStatusFilter('all');
    setHighRiskOnly(false);
  };

  if (status === 'loading') return <LoadingState message="加载运行列表..." />;
  if (status === 'error') return <ErrorState message={error.message} onRetry={refetch} />;

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Runs" description="所有 Agent 运行记录" />
      <div className="p-6 space-y-4">
        <FilterBar
          search={search}
          onSearchChange={setSearch}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          highRiskOnly={highRiskOnly}
          onHighRiskOnlyChange={setHighRiskOnly}
          onClear={clearFilters}
        />
        {runs && runs.length === 0 ? (
          <EmptyState title="暂无运行记录" description="运行 traceseal run 来生成第一条记录" />
        ) : (
          <RunsTable runs={filtered} onRowClick={(id) => navigate(`/runs/${id}`)} />
        )}
      </div>
    </div>
  );
}