import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useAsync } from '../hooks/useAsync';
import { getTraceSealApi } from '../api';
import { StatCard, RunsTable, LoadingState, ErrorState, EmptyState, RiskBadge } from '../components';
import { useWorkspace } from '../workspace';

export function HomePage() {
  const api = useMemo(() => getTraceSealApi(), []);
  const { revision } = useWorkspace();
  const latestRun = useAsync(() => api.getLatestRun(), [api, revision]);
  const runsList = useAsync(() => api.listRuns(), [api, revision]);

  // Loading
  if (latestRun.status === 'loading' && runsList.status === 'loading') {
    return <LoadingState message="加载仪表盘..." />;
  }

  // Error
  if (latestRun.status === 'error' && runsList.status === 'error') {
    return <ErrorState message="加载失败" onRetry={() => { latestRun.refetch(); runsList.refetch(); }} />;
  }

  const run = latestRun.data;
  const runs = runsList.data ?? [];

  const totalEvents = runs.reduce((sum, r) => sum + r.event_count, 0);
  const totalHighRisk = runs.reduce((sum, r) => sum + r.high_risk_count, 0);
  const blockedCount = runs.filter((r) => r.status === 'blocked').length;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-100">Dashboard</h2>
        <p className="text-xs text-gray-500 mt-1">AI Agent 操作黑匣子运行概览</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="总运行次数" value={runs.length} />
        <StatCard label="总事件数" value={totalEvents} />
        <StatCard label="高风险事件" value={totalHighRisk} variant={totalHighRisk > 0 ? 'danger' : 'default'} />
        <StatCard label="已阻断" value={blockedCount} variant={blockedCount > 0 ? 'warning' : 'default'} />
      </div>

      {/* Latest run card */}
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
        <h3 className="text-sm font-medium text-gray-200 mb-3">最近运行</h3>
        {runsList.status === 'success' && runs.length === 0 ? (
          <EmptyState title="暂无运行记录" description="当前工作区还没有 Runs，运行 traceseal run 来生成第一条记录" />
        ) : latestRun.status === 'error' ? (
          <div className="flex items-center gap-2 text-red-400 text-xs">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
            获取最近运行失败
            <button onClick={latestRun.refetch} className="underline ml-2">重试</button>
          </div>
        ) : run ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-xs font-mono text-gray-300">{run.run_id}</span>
              <span className="text-xs text-gray-500">{run.command}</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">事件:</span>
                <span className="text-xs text-gray-200">{run.event_count}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">高风险:</span>
                <span className={`text-xs font-medium ${run.high_risk_count > 0 ? 'text-red-400' : 'text-gray-400'}`}>
                  {run.high_risk_count}
                </span>
              </div>
              {run.first_harmful_event && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">First Harmful:</span>
                  <RiskBadge level={run.first_harmful_event.risk?.level} />
                  <span className="text-xs font-mono text-gray-400">{run.first_harmful_event.id}</span>
                </div>
              )}
              {!run.first_harmful_event && (
                <span className="text-xs text-gray-600">无有害事件</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Link
                to={`/runs/${run.run_id}`}
                className="text-xs text-emerald-400 hover:text-emerald-300 px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                查看详情
              </Link>
              {run.first_harmful_event && (
                <Link
                  to={`/runs/${run.run_id}/explain`}
                  className="text-xs text-orange-400 hover:text-orange-300 px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  explain
                </Link>
              )}
            </div>
          </div>
        ) : (
          <EmptyState title="暂无运行记录" description="当前工作区还没有 Runs，运行 traceseal run 来生成第一条记录" />
        )}
      </div>

      {/* Recent runs */}
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-200">最近运行</h3>
          <Link to="/runs" className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
            查看全部
          </Link>
        </div>
        {runsList.status === 'error' ? (
          <div className="text-xs text-red-400">加载失败</div>
        ) : runs.length === 0 ? (
          <EmptyState title="暂无运行记录" description="当前工作区还没有 Runs，运行 traceseal run 来生成第一条记录" />
        ) : (
          <RunsTable runs={runs.slice(0, 5)} />
        )}
      </div>
    </div>
  );
}
