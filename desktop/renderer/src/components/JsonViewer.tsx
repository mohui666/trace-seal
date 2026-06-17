interface JsonViewerProps {
  data: unknown;
  maxHeight?: string;
}

export function JsonViewer({ data, maxHeight = '300px' }: JsonViewerProps) {
  const json = JSON.stringify(data, null, 2);

  return (
    <div
      className="overflow-auto rounded-lg bg-gray-950 border border-gray-800"
      style={{ maxHeight }}
    >
      <pre className="p-3 text-xs font-mono text-gray-300 leading-relaxed whitespace-pre-wrap break-all">
        {json}
      </pre>
    </div>
  );
}