import { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAsync } from '../hooks/useAsync';
import { getTraceSealApi } from '../api';
import { EventTimeline, LoadingState, ErrorState, PageHeader, RunStatusBadge, RiskBadge } from '../components';

export function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const api = useMemo(() => getTraceSealApi(), []);
  const { status, data: run, error, refetch } = useAsync(
    () => api.getRun(id!),
    [api, id],
    { enabled: !!id }
  );

  if (!id) return <ErrorState message="缺少 Run ID" />;
  if (status === 'loading') return <LoadingState message={`加载 ${id}...`} />;
  if (status === 'error') return <ErrorState message={error.message} onRetry={refetch} />;
  if (!run) return <ErrorState message="未找到运行记录" />;

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Run Detail" description={run.run_id}>
        <Link
          to={`/runs/${run.run_id}/explain`}
          className="text-xs text-orange-400 hover:text-orange-300 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          explain
        </Link>
      </PageHeader>

      <div className="p-6 space-y-6">
        {/* Run summary */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h3 className="text-sm font-medium text-gray-200 mb-4">运行概要</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500">Run ID</p>
              <p className="text-xs font-mono text-gray-200 mt-1">{run.run_id}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Status</p>
              <div className="mt-1"><RunStatusBadge status={run.status} /></div>
            </div>
            <div>
              <p className="text-xs text-gray-500">Exit Code</p>
              <p className={`text-xs font-mono mt-1 ${run.exit_code === 0 ? 'text-green-400' : run.exit_code !== undefined ? 'text-red-400' : 'text-gray-500'}`}>
                {run.exit_code ?? '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Events</p>
              <p className="text-xs font-mono text-gray-200 mt-1">{run.event_count} / {run.high_risk_count} 高风险</p>
            </div>
            <div className="col-span-2">
              <p className="text-xs text-gray-500">Command</p>
              <code className="block text-xs font-mono text-gray-300 mt-1 break-all">{run.command}</code>
            </div>
            <div>
              <p className="text-xs text-gray-500">Started</p>
              <p className="text-xs text-gray-400 mt-1">{run.started_at ? new Date(run.started_at).toLocaleString('zh-CN') : '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Finished</p>
              <p className="text-xs text-gray-400 mt-1">{run.finished_at ? new Date(run.finished_at).toLocaleString('zh-CN') : '-'}</p>
            </div>
          </div>

          {run.first_harmful_event && (
            <div className="mt-4 pt-4 border-t border-gray-800">
              <p className="text-xs text-gray-500 mb-2">First Harmful Event</p>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-gray-300">{run.first_harmful_event.id}</span>
                <RiskBadge level={run.first_harmful_event.risk?.level} />
                <span className="text-xs text-gray-400">{run.first_harmful_event.operation ?? run.first_harmful_event.type}</span>
              </div>
            </div>
          )}
        </div>

        {/* Event timeline */}
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-5">
          <h3 className="text-sm font-medium text-gray-200 mb-4">事件时间线</h3>
          <EventTimeline events={run.events} />
        </div>
      </div>
    </div>
  );
}