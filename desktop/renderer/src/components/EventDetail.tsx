import { useState } from 'react';
import type { TraceEvent } from '../api';
import { RiskBadge } from './RiskBadge';
import { FileDiff } from './FileDiff';
import { ShellOutput } from './ShellOutput';
import { HttpDetail } from './HttpDetail';
import { JsonViewer } from './JsonViewer';

interface EventDetailProps {
  event: TraceEvent;
}

export function EventDetail({ event }: EventDetailProps) {
  const [showRaw, setShowRaw] = useState(false);

  const isFile = event.type === 'file.write' || event.type === 'file.delete';
  const isShell = event.type === 'shell';
  const isHttp = event.type === 'http';

  const riskLevel = event.risk?.level;
  const policyRule = event.risk?.policy_rule;
  const reasons = event.risk?.reasons;
  const action = event.risk?.action;

  return (
    <div className="space-y-4">
      {/* Risk info */}
      {(riskLevel || policyRule || reasons) && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            {riskLevel && <RiskBadge level={riskLevel} />}
            {policyRule && (
              <span className="text-xs font-mono text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">
                {policyRule}
              </span>
            )}
            {action && (
              <span className="text-xs text-gray-400">
                action: {action}
              </span>
            )}
          </div>
          {reasons && reasons.length > 0 && (
            <ul className="space-y-0.5">
              {reasons.map((r, i) => (
                <li key={i} className="text-xs text-gray-400 flex items-start gap-2">
                  <span className="text-gray-600 mt-1">•</span>
                  {r}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Type-specific detail */}
      {isFile && (
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium">文件</p>
          <p className="text-xs font-mono text-gray-200 mb-2">{event.input?.path as string ?? 'unknown'}</p>
          {event.file_changes && <FileDiff changes={event.file_changes} />}
        </div>
      )}

      {isShell && (
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium">Shell</p>
          <ShellOutput input={event.input} output={event.output} />
        </div>
      )}

      {isHttp && (
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium">HTTP</p>
          <HttpDetail input={event.input} output={event.output} />
        </div>
      )}

      {/* Raw JSON toggle */}
      <div>
        <button
          onClick={() => setShowRaw(!showRaw)}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors focus:outline-none focus:underline"
          aria-expanded={showRaw}
        >
          {showRaw ? '收起 Raw JSON' : '查看 Raw JSON'}
        </button>
        {showRaw && (
          <div className="mt-2">
            <JsonViewer data={event} />
          </div>
        )}
      </div>
    </div>
  );
}