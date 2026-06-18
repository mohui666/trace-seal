import { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAsync } from '../hooks/useAsync';
import { getTraceSealApi } from '../api';
import { ExplainPanel, LoadingState, ErrorState, PageHeader } from '../components';
import { useWorkspace } from '../workspace';

export function ExplainPage() {
  const { id } = useParams<{ id: string }>();
  const api = useMemo(() => getTraceSealApi(), []);
  const { revision } = useWorkspace();
  const { status, data: run, error, refetch } = useAsync(
    () => api.getRun(id!),
    [api, id, revision],
    { enabled: !!id }
  );

  if (!id) return <ErrorState message="缺少 Run ID" />;
  if (status === 'loading') return <LoadingState message={`分析 ${id}...`} />;
  if (status === 'error') return <ErrorState message={error.message} onRetry={refetch} />;
  if (!run) return <ErrorState message="未找到运行记录" />;

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Explain" description={`${run.run_id} — 事故分析`}>
        <Link
          to={`/runs/${run.run_id}`}
          className="text-xs text-emerald-400 hover:text-emerald-300 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          ← 返回详情
        </Link>
      </PageHeader>

      <div className="p-6 max-w-3xl">
        <ExplainPanel
          firstHarmfulEvent={run.first_harmful_event}
          affectedFiles={run.affected_files}
          suggestedPolicy={run.suggested_policy}
        />
      </div>
    </div>
  );
}
