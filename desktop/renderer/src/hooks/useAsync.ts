import { useState, useEffect, useCallback, useRef } from 'react';

type AsyncState<T> =
  | { status: 'loading'; data: null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: null; error: Error };

interface UseAsyncOptions {
  enabled?: boolean;
}

export function useAsync<T>(
  fn: () => Promise<T>,
  deps: unknown[] = [],
  options: UseAsyncOptions = {}
) {
  const { enabled = true } = options;
  const [state, setState] = useState<AsyncState<T>>({
    status: 'loading',
    data: null,
    error: null,
  });
  const mountedRef = useRef(true);
  const fnRef = useRef(fn);

  // Keep fnRef updated
  fnRef.current = fn;

  const execute = useCallback(async () => {
    setState({ status: 'loading', data: null, error: null });
    try {
      const result = await fnRef.current();
      if (mountedRef.current) {
        setState({ status: 'success', data: result, error: null });
      }
    } catch (err) {
      if (mountedRef.current) {
        setState({ status: 'error', data: null, error: err instanceof Error ? err : new Error(String(err)) });
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled) {
      execute();
    }
    return () => {
      mountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, enabled]);

  return { ...state, refetch: execute };
}