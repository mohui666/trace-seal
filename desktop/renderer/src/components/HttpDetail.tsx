interface HttpDetailProps {
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
}

export function HttpDetail({ input, output }: HttpDetailProps) {
  const method = (input?.method as string) ?? 'GET';
  const url = (input?.url as string) ?? 'unknown';
  const statusCode = output?.status_code as number | undefined;
  const error = output?.error as string;

  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs text-gray-500 mb-1">请求</p>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
            method === 'GET' ? 'bg-blue-900/30 text-blue-400' :
            method === 'POST' ? 'bg-green-900/30 text-green-400' :
            method === 'PUT' ? 'bg-yellow-900/30 text-yellow-400' :
            'bg-gray-800 text-gray-300'
          }`}>
            {method}
          </span>
          <code className="text-xs font-mono text-gray-300 break-all">{url}</code>
        </div>
      </div>
      {statusCode !== undefined && (
        <div>
          <p className="text-xs text-gray-500 mb-1">状态码</p>
          <span className={`text-xs font-mono font-medium ${statusCode < 400 ? 'text-green-400' : 'text-red-400'}`}>
            {statusCode}
          </span>
        </div>
      )}
      {error && (
        <div>
          <p className="text-xs text-gray-500 mb-1">错误</p>
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}
    </div>
  );
}