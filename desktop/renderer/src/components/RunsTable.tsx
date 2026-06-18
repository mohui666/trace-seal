import { Link } from 'react-router-dom';
import type { RunSummary } from '../api';
import { RunStatusBadge } from './RunStatusBadge';
import { formatDate, formatCommand } from '../utils/safety';

interface RunsTableProps {
  runs: RunSummary[];
  onRowClick?: (runId: string) => void;
}

export function RunsTable({ runs, onRowClick }: RunsTableProps) {
  if (!runs.length) {
    return (
      <div className="text-center py-8">
        <p className="text-xs text-gray-500">暂无运行记录</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs" role="table" aria-label="运行列表">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="text-left py-2 px-3 text-gray-500 font-medium">Run ID</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">命令</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">开始时间</th>
            <th className="text-left py-2 px-3 text-gray-500 font-medium">状态</th>
            <th className="text-right py-2 px-3 text-gray-500 font-medium">退出码</th>
            <th className="text-right py-2 px-3 text-gray-500 font-medium">事件数</th>
            <th className="text-right py-2 px-3 text-gray-500 font-medium">高风险</th>
            <th className="text-right py-2 px-3 text-gray-500 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr
              key={run.run_id}
              className="border-b border-gray-800/50 hover:bg-gray-900/50 transition-colors cursor-pointer"
              onClick={() => onRowClick?.(run.run_id)}
              tabIndex={0}
              role="row"
              onKeyDown={(e) => {
                if (e.key === 'Enter') onRowClick?.(run.run_id);
              }}
            >
              <td className="py-2 px-3 font-mono text-gray-300 max-w-[160px] truncate" title={run.run_id}>
                {run.run_id}
              </td>
              <td className="py-2 px-3 text-gray-400 max-w-[300px] truncate" title={run.command}>
                {formatCommand(run.command)}
              </td>
              <td className="py-2 px-3 text-gray-500 whitespace-nowrap">
                {formatDate(run.started_at)}
              </td>
              <td className="py-2 px-3">
                <RunStatusBadge status={run.status} />
              </td>
              <td className="py-2 px-3 text-right font-mono">
                <span className={run.exit_code === 0 ? 'text-green-400' : run.exit_code !== undefined ? 'text-red-400' : 'text-gray-500'}>
                  {run.exit_code ?? '-'}
                </span>
              </td>
              <td className="py-2 px-3 text-right text-gray-400">{run.event_count}</td>
              <td className="py-2 px-3 text-right">
                <span className={run.high_risk_count > 0 ? 'text-red-400 font-medium' : 'text-gray-500'}>
                  {run.high_risk_count}
                </span>
              </td>
              <td className="py-2 px-3 text-right">
                <div className="flex items-center gap-1 justify-end">
                  <Link
                    to={`/runs/${run.run_id}`}
                    className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors px-2 py-0.5 rounded hover:bg-gray-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    onClick={(e) => e.stopPropagation()}
                    aria-label={`查看 ${run.run_id} 详情`}
                  >
                    查看
                  </Link>
                  {run.first_harmful_event_id && (
                    <Link
                      to={`/runs/${run.run_id}/explain`}
                      className="text-xs text-orange-400 hover:text-orange-300 transition-colors px-2 py-0.5 rounded hover:bg-gray-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      onClick={(e) => e.stopPropagation()}
                      aria-label={`查看 ${run.run_id} 分析`}
                    >
                      explain
                    </Link>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}