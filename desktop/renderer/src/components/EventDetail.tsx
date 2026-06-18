import { useState } from 'react';
import type { TraceEvent } from '../api';
import { RiskBadge } from './RiskBadge';
import { FileDiff } from './FileDiff';
import { ShellOutput } from './ShellOutput';
import { HttpDetail } from './HttpDetail';
import { JsonViewer } from './JsonViewer';
import { getEventPrimaryInput, getEventOutputStatus } from '../utils/safety';

interface EventDetailProps {
  event: TraceEvent;
}

export function EventDetail({ event }: EventDetailProps) {
  const [showRaw, setShowRaw] = useState(false);

  const isFile = event.type === 'file.write' || event.type === 'file.delete';
  const isShell = event.type === 'shell';
  const isHttp = event.type === 'http';
  const isSdk = event.type === 'sdk';
  const isKnown = isFile || isShell || isHttp || isSdk;

  const riskLevel = event.risk?.level;
  const policyRule = event.risk?.policy_rule;
  const reasons = event.risk?.reasons;
  const action = event.risk?.action;
  const primaryInput = getEventPrimaryInput(event);
  const outputStatus = getEventOutputStatus(event);

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
          <p className="text-xs font-mono text-gray-200 mb-2">{primaryInput}</p>
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

      {isSdk && (
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium">SDK</p>
          <div className="space-y-2">
            <div>
              <p className="text-xs text-gray-600 mb-1">操作</p>
              <code className="text-xs font-mono text-gray-300 break-all">{primaryInput}</code>
            </div>
            {outputStatus && (
              <div>
                <p className="text-xs text-gray-600 mb-1">输出状态</p>
                <span className={`text-xs font-mono ${outputStatus === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
                  {outputStatus}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Generic panel for unknown event types */}
      {!isKnown && (
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium">通用事件详情</p>
          <div className="space-y-2">
            <div>
              <p className="text-xs text-gray-600 mb-1">类型</p>
              <code className="text-xs font-mono text-gray-300">{event.type}</code>
            </div>
            {event.operation && (
              <div>
                <p className="text-xs text-gray-600 mb-1">操作</p>
                <code className="text-xs font-mono text-gray-300 break-all">{event.operation}</code>
              </div>
            )}
            <div>
              <p className="text-xs text-gray-600 mb-1">主要输入</p>
              <code className="text-xs font-mono text-gray-300 break-all">{primaryInput}</code>
            </div>
            {event.input && Object.keys(event.input).length > 0 && (
              <div>
                <p className="text-xs text-gray-600 mb-1">Input</p>
                <JsonViewer data={event.input} maxHeight="150px" />
              </div>
            )}
            {event.output && Object.keys(event.output).length > 0 && (
              <div>
                <p className="text-xs text-gray-600 mb-1">Output</p>
                <JsonViewer data={event.output} maxHeight="150px" />
              </div>
            )}
            {event.file_changes && event.file_changes.length > 0 && (
              <div>
                <p className="text-xs text-gray-600 mb-1">文件变更</p>
                <FileDiff changes={event.file_changes} />
              </div>
            )}
          </div>
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