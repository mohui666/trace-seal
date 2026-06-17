import type { TraceEvent } from '../api';
import { RiskBadge } from './RiskBadge';
import { CopyButton } from './CopyButton';

interface ExplainPanelProps {
  firstHarmfulEvent?: TraceEvent | null;
  affectedFiles?: string[];
  suggestedPolicy?: string | null;
}

export function ExplainPanel({
  firstHarmfulEvent,
  affectedFiles = [],
  suggestedPolicy,
}: ExplainPanelProps) {
  if (!firstHarmfulEvent) {
    return (
      <div className="rounded-lg border border-green-800 bg-green-950/20 p-6" role="status">
        <div className="flex items-center gap-3">
          <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-sm font-medium text-green-400">未发现有害调用</p>
            <p className="text-xs text-gray-500 mt-1">本次运行中没有检测到高风险操作。</p>
          </div>
        </div>
      </div>
    );
  }

  const riskLevel = firstHarmfulEvent.risk?.level;
  const reasons = firstHarmfulEvent.risk?.reasons ?? [];
  const policyRule = firstHarmfulEvent.risk?.policy_rule;
  const eventType = firstHarmfulEvent.type;
  const operation = firstHarmfulEvent.operation ?? firstHarmfulEvent.input?.command as string ?? 'unknown';

  return (
    <div className="space-y-4">
      {/* First harmful event card */}
      <div className="rounded-lg border border-red-800 bg-red-950/20 p-6">
        <div className="flex items-center gap-2 mb-3">
          <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h3 className="text-sm font-semibold text-red-400">First Harmful Tool Call</h3>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-gray-400">{firstHarmfulEvent.id}</span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">{eventType}</span>
            {riskLevel && <RiskBadge level={riskLevel} />}
            {policyRule && (
              <span className="text-xs font-mono text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">
                {policyRule}
              </span>
            )}
          </div>

          <p className="text-sm font-mono text-gray-200 break-all">{operation}</p>
        </div>
      </div>

      {/* Reasons */}
      {reasons.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <h4 className="text-xs font-medium text-gray-400 mb-2">Reasons</h4>
          <ul className="space-y-1">
            {reasons.map((r, i) => (
              <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                <span className="text-gray-600 mt-1">•</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Affected files */}
      {affectedFiles.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <h4 className="text-xs font-medium text-gray-400 mb-2">Affected Files</h4>
          <ul className="space-y-1">
            {affectedFiles.map((f, i) => (
              <li key={i} className="text-xs font-mono text-gray-300">{f}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggested policy */}
      {suggestedPolicy && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-medium text-gray-400">Suggested Policy</h4>
            <CopyButton text={suggestedPolicy} label="复制规则" />
          </div>
          <pre className="text-xs font-mono text-gray-300 bg-gray-950 p-3 rounded border border-gray-800 overflow-auto max-h-40 whitespace-pre-wrap">
            {suggestedPolicy}
          </pre>
        </div>
      )}
    </div>
  );
}