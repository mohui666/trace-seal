interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = '加载失败', onRetry }: ErrorStateProps) {
  return (
    <div className="flex items-center justify-center py-16" role="alert">
      <div className="flex flex-col items-center gap-3 text-center">
        <svg className="w-12 h-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <div>
          <p className="text-sm font-medium text-red-400">{message}</p>
          <p className="text-xs text-gray-600 mt-1">请检查连接后重试</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 px-4 py-1.5 text-xs font-medium bg-gray-800 text-gray-200 rounded-lg hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            重试
          </button>
        )}
      </div>
    </div>
  );
}