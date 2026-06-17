import type { FileChange } from '../api';

interface FileDiffProps {
  changes: FileChange[];
}

function changeLabel(type: FileChange['change_type']): string {
  switch (type) {
    case 'created': return '创建';
    case 'modified': return '修改';
    case 'deleted': return '删除';
  }
}

function changeColor(type: FileChange['change_type']): string {
  switch (type) {
    case 'created': return 'text-green-400';
    case 'modified': return 'text-yellow-400';
    case 'deleted': return 'text-red-400';
  }
}

export function FileDiff({ changes }: FileDiffProps) {
  if (!changes.length) return <p className="text-xs text-gray-500">无文件变更</p>;

  return (
    <div className="space-y-1">
      {changes.map((change, i) => (
        <div key={i} className="flex items-center gap-2 text-xs font-mono py-1 px-2 rounded bg-gray-900/50">
          <span className={`font-medium ${changeColor(change.change_type)}`}>
            {changeLabel(change.change_type)}
          </span>
          <span className="text-gray-300 truncate">{change.path}</span>
          {change.before_sha256 && (
            <span className="text-gray-600 text-[10px] ml-auto" title={change.before_sha256}>
              {change.before_sha256.slice(0, 8)}
            </span>
          )}
          {change.after_sha256 && (
            <span className="text-gray-600 text-[10px]" title={change.after_sha256}>
              → {change.after_sha256.slice(0, 8)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}