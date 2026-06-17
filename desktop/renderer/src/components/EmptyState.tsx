export function EmptyState({
  title = '暂无数据',
  description = '没有找到相关记录',
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex items-center justify-center py-16" role="status">
      <div className="flex flex-col items-center gap-3 text-center">
        <svg className="w-12 h-12 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <div>
          <p className="text-sm font-medium text-gray-400">{title}</p>
          <p className="text-xs text-gray-600 mt-1">{description}</p>
        </div>
      </div>
    </div>
  );
}