import { formatCommand } from '../utils/safety';

interface ShellOutputProps {
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
}

export function ShellOutput({ input, output }: ShellOutputProps) {
  const command = (input?.command as string) ?? 'unknown';
  const returncode = output?.returncode as number | undefined;
  const stdout = (output?.stdout as string) ?? (output?.output as string);
  const stderr = output?.stderr as string;

  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs text-gray-500 mb-1">命令</p>
        <code className="block text-xs font-mono bg-gray-950 text-gray-200 px-3 py-2 rounded border border-gray-800 break-all" title={command}>
          {formatCommand(command, 200)}
        </code>
      </div>
      {returncode !== undefined && (
        <div>
          <p className="text-xs text-gray-500 mb-1">退出码</p>
          <span className={`text-xs font-mono font-medium ${returncode === 0 ? 'text-green-400' : 'text-red-400'}`}>
            {returncode}
          </span>
        </div>
      )}
      {stdout && (
        <div>
          <p className="text-xs text-gray-500 mb-1">stdout</p>
          <pre className="text-xs font-mono bg-gray-950 text-gray-300 px-3 py-2 rounded border border-gray-800 overflow-auto max-h-40 whitespace-pre-wrap break-all">
            {stdout}
          </pre>
        </div>
      )}
      {stderr && (
        <div>
          <p className="text-xs text-gray-500 mb-1">stderr</p>
          <pre className="text-xs font-mono bg-gray-950 text-red-400 px-3 py-2 rounded border border-red-900/50 overflow-auto max-h-40 whitespace-pre-wrap break-all">
            {stderr}
          </pre>
        </div>
      )}
    </div>
  );
}