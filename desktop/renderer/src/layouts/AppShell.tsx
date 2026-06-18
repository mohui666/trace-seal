import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useWorkspace } from '../workspace';

function Sidebar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
      isActive
        ? 'bg-gray-800 text-emerald-400 font-medium'
        : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
    }`;

  return (
    <aside className="w-56 flex-shrink-0 border-r border-gray-800 bg-gray-950 flex flex-col">
      <div className="px-4 py-5 border-b border-gray-800">
        <h1 className="text-lg font-bold text-emerald-400 tracking-tight">TraceSeal</h1>
        <p className="text-xs text-gray-500 mt-0.5">Dashboard</p>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1" aria-label="主导航">
        <NavLink to="/" className={linkClass} end>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
          首页
        </NavLink>
        <NavLink to="/runs" className={linkClass}>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
          Runs
        </NavLink>
        <NavLink to="/policy" className={linkClass}>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          Policy
        </NavLink>
      </nav>
      <div className="px-3 py-4 border-t border-gray-800">
        <p className="text-xs text-gray-600">v0.2.0</p>
      </div>
    </aside>
  );
}

function TopBar() {
  const { workspace, busy, isLive, selectWorkspace, clearWorkspace } = useWorkspace();
  const navigate = useNavigate();

  const chooseWorkspace = async () => {
    try {
      const previousPath = workspace.path;
      const selected = await selectWorkspace();
      if (selected.valid && selected.path && selected.path !== previousPath) navigate('/');
    } catch {
      // WorkspaceContext renders the structured error state.
    }
  };

  const clear = async () => {
    try {
      await clearWorkspace();
      navigate('/');
    } catch {
      // WorkspaceContext renders the structured error state.
    }
  };

  return (
    <header className="min-h-14 border-b border-gray-800 bg-gray-950 flex items-center justify-between gap-4 px-6 py-2 flex-shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-yellow-500'}`}
            aria-hidden="true"
          />
          <span className="text-xs text-gray-400">
            {isLive ? 'Live Electron' : 'Mock Data'}
          </span>
        </div>
        {isLive && (
          <div className="min-w-0 border-l border-gray-800 pl-3">
            <p className="text-[10px] text-gray-600">当前工作区</p>
            <p className={`text-xs truncate max-w-[520px] ${workspace.valid ? 'text-gray-300' : 'text-amber-400'}`} title={workspace.path ?? undefined}>
              {workspace.path ?? '尚未选择'}
            </p>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {isLive && (
          <>
            <button
              type="button"
              onClick={() => void chooseWorkspace()}
              disabled={busy}
              className="px-3 py-1.5 text-xs rounded-lg border border-emerald-800 text-emerald-400 hover:bg-emerald-950/40 disabled:opacity-50"
            >
              {workspace.valid ? '切换工作区' : '选择工作区'}
            </button>
            {workspace.path && (
              <button
                type="button"
                onClick={() => void clear()}
                disabled={busy}
                className="px-3 py-1.5 text-xs rounded-lg border border-gray-700 text-gray-400 hover:bg-gray-800 disabled:opacity-50"
              >
                清除工作区
              </button>
            )}
          </>
        )}
        <span className="text-xs text-gray-500 ml-2">TraceSeal Dashboard</span>
      </div>
    </header>
  );
}

function WorkspacePrompt() {
  const { workspace, status, error, busy, selectWorkspace, reloadWorkspace } = useWorkspace();

  if (status === 'loading') {
    return <div className="h-full grid place-items-center text-sm text-gray-400">正在读取工作区设置...</div>;
  }

  if (status === 'error') {
    return (
      <div className="h-full grid place-items-center p-8">
        <div className="max-w-lg w-full rounded-xl border border-red-900/60 bg-red-950/20 p-6 text-center">
          <h2 className="text-base font-semibold text-red-300">工作区 API 出错</h2>
          <p className="text-xs text-red-400/80 mt-2 break-all">{error?.message ?? '未知错误'}</p>
          <button onClick={() => void reloadWorkspace()} className="mt-4 px-4 py-2 text-xs rounded-lg bg-gray-800 text-gray-200 hover:bg-gray-700">重试</button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full grid place-items-center p-8">
      <div className="max-w-xl w-full rounded-xl border border-gray-800 bg-gray-900 p-8 text-center shadow-2xl">
        <div className="mx-auto w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-900 grid place-items-center text-emerald-400 text-xl">⌂</div>
        <h2 className="text-lg font-semibold text-gray-100 mt-4">
          {workspace.path ? '工作区无效' : '选择 TraceSeal 工作区'}
        </h2>
        <p className="text-sm text-gray-500 mt-2">
          {workspace.path
            ? '保存的目录不存在或当前无法访问，请重新选择一个目录。'
            : '选择用于保存 runs 和 policy 的项目目录。空目录也可以作为新工作区。'}
        </p>
        {workspace.path && <p className="text-xs font-mono text-amber-400 mt-3 break-all">{workspace.path}</p>}
        <button
          type="button"
          onClick={() => void selectWorkspace().catch(() => undefined)}
          disabled={busy}
          className="mt-6 px-5 py-2.5 text-sm rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {busy ? '正在选择...' : workspace.path ? '重新选择工作区' : '选择工作区'}
        </button>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children?: ReactNode }) {
  const { workspace, isLive } = useWorkspace();
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-950">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-auto">
          {isLive && !workspace.valid ? <WorkspacePrompt /> : (children ?? <Outlet />)}
        </main>
      </div>
    </div>
  );
}
