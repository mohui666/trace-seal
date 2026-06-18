import { useState, useCallback } from 'react';

interface CopyButtonProps {
  text: string;
  label?: string;
}

export function CopyButton({ text, label = '复制' }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);

  const handleCopy = useCallback(async () => {
    if (!text) return;
    setFailed(false);
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setFailed(true);
      setTimeout(() => setFailed(false), 2000);
    }
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      disabled={!text}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
        copied
          ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-800'
          : failed
          ? 'bg-red-900/30 text-red-400 border border-red-800'
          : 'bg-gray-800 text-gray-300 border border-gray-700 hover:bg-gray-700 hover:text-gray-100'
      }`}
      aria-label={copied ? '已复制' : failed ? '复制失败' : label}
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          已复制
        </>
      ) : failed ? (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          复制失败
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}