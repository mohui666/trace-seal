import { useState } from 'react';
import type { TraceEvent } from '../api';
import { RiskBadge } from './RiskBadge';
import { EventDetail } from './EventDetail';
import { getEventOutputStatus, formatTime } from '../utils/safety';

interface EventTimelineProps {
  events: TraceEvent[];
}

export function EventTimeline({ events }: EventTimelineProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!events.length) {
    return <p className="text-xs text-gray-500 py-4">无事件记录</p>;
  }

  return (
    <div className="relative">
      {/* vertical line */}
      <div className="absolute left-3 top-2 bottom-2 w-px bg-gray-800" aria-hidden="true" />

      <div className="space-y-1">
        {events.map((event) => {
          const isExpanded = expandedId === event.id;
          const hasRisk = !!event.risk?.level;
          const isHarmful = hasRisk && (event.risk?.level === 'high' || event.risk?.level === 'critical');
          const outputStatus = getEventOutputStatus(event);

          return (
            <div key={event.id} className={`relative pl-8 pr-2 py-1.5 rounded ${isHarmful ? 'bg-red-950/20 border border-red-900/30' : ''}`}>
              {/* dot */}
              <div
                className={`absolute left-2 top-3 w-2.5 h-2.5 rounded-full border-2 ${
                  isHarmful
                    ? 'bg-red-500 border-red-500'
                    : hasRisk
                    ? 'bg-yellow-500 border-yellow-500'
                    : 'bg-gray-700 border-gray-700'
                }`}
                aria-hidden="true"
              />

              <button
                onClick={() => setExpandedId(isExpanded ? null : event.id)}
                className="w-full text-left focus:outline-none focus:ring-1 focus:ring-emerald-500 rounded"
                aria-expanded={isExpanded}
                aria-label={`事件 ${event.seq ?? event.id}: ${event.operation ?? event.type}`}
              >
                <div className="flex items-center gap-2 flex-wrap min-w-0">
                  <span className="text-xs font-mono text-gray-500 shrink-0">
                    #{event.seq ?? event.id}
                  </span>
                  <span className="text-xs font-mono font-medium text-gray-300 shrink-0">
                    {event.type}
                  </span>
                  <span className="text-xs text-gray-400 truncate">
                    {event.operation ?? ''}
                  </span>
                  {event.risk?.level && <RiskBadge level={event.risk.level} />}
                  {event.file_changes && event.file_changes.length > 0 && (
                    <span className="text-xs text-gray-600 ml-auto shrink-0">
                      {event.file_changes.length} 文件
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-gray-600 font-mono">{event.id}</span>
                  {event.ts && <span className="text-[10px] text-gray-600">{formatTime(event.ts)}</span>}
                  {outputStatus && (
                    <span className={`text-[10px] ${outputStatus === 'ok' ? 'text-gray-600' : 'text-red-400'}`}>
                      {outputStatus}
                    </span>
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="mt-2 pt-2 border-t border-gray-800">
                  <EventDetail event={event} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}