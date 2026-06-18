import { HashRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './layouts/AppShell';
import { HomePage } from './pages/HomePage';
import { RunsPage } from './pages/RunsPage';
import { RunDetailPage } from './pages/RunDetailPage';
import { ExplainPage } from './pages/ExplainPage';
import { PolicyPage } from './pages/PolicyPage';
import { WorkspaceProvider } from './workspace';

export function App() {
  return (
    <HashRouter>
      <WorkspaceProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<HomePage />} />
            <Route path="runs" element={<RunsPage />} />
            <Route path="runs/:id" element={<RunDetailPage />} />
            <Route path="runs/:id/explain" element={<ExplainPage />} />
            <Route path="policy" element={<PolicyPage />} />
          </Route>
        </Routes>
      </WorkspaceProvider>
    </HashRouter>
  );
}
