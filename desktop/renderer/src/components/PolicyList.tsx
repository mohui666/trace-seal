import type { PolicyRule, RiskLevel, PolicyAction } from '../api';
import { RiskBadge } from './RiskBadge';
import { CopyButton } from './CopyButton';

interface PolicyListProps {
  rules: PolicyRule[];
  riskFilter?: RiskLevel | 'all';
  actionFilter?: PolicyAction | 'all';
}

export function PolicyList({ rules, riskFilter = 'all', actionFilter = 'all' }: PolicyListProps) {
  const filtered = rules.filter((r) => {
    if (riskFilter !== 'all' && r.risk_level !== riskFilter) return false;
    if (actionFilter !== 'all' && r.action !== actionFilter) return false;
    return true;
  });

  if (!filtered.length) {
    return <p className="text-xs text-gray-500 py-8 text-center">没有匹配的规则</p>;
  }

  return (
    <div className="space-y-3">
      {filtered.map((rule) => (
        <div key={rule.rule_id} className="rounded-lg border border-gray-800 bg-gray-900 p-4">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="text-sm font-mono font-medium text-gray-200">{rule.rule_id}</span>
            {rule.risk_level && <RiskBadge level={rule.risk_level} />}
            {rule.action && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 font-mono">
                {rule.action}
              </span>
            )}
            {rule.event_type && (
              <span className="text-xs text-gray-500 ml-auto">{rule.event_type}</span>
            )}
          </div>
          {rule.pattern && (
            <p className="text-xs text-gray-500 mt-1">
              <span className="text-gray-600">匹配: </span>
              <code className="text-gray-400">{rule.pattern}</code>
            </p>
          )}
          {rule.description && (
            <p className="text-xs text-gray-400 mt-1.5">{rule.description}</p>
          )}
          {rule.suggested_policy && (
            <div className="mt-2 flex items-center justify-between">
              <code className="text-xs font-mono text-gray-500 truncate max-w-[300px]">
                {rule.suggested_policy}
              </code>
              <CopyButton text={rule.suggested_policy} label="复制" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}