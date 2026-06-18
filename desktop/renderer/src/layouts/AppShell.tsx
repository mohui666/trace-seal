import { NavLink, Outlet } from 'react-router-dom';
import type { ReactNode } from 'react';
import { isElectronEnv } from '../utils/safety';

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
        <p className="text-xs text-gray-600">v0.2.0-dev</p>
      </div>
    </aside>
  );
}

function TopBar() {
  const isLive = isElectronEnv();

  return (
    <header className="h-12 border-b border-gray-800 bg-gray-950 flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-yellow-500'}`}
          aria-hidden="true"
        />
        <span className="text-xs text-gray-400">
          {isLive ? 'Live Electron' : 'Mock Data'}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-xs text-gray-500">TraceSeal Dashboard</span>
      </div>
    </header>
  );
}

export function AppShell({ children }: { children?: ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-950">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-auto">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  );
}