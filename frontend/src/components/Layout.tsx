import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Bug,
  GitCommitHorizontal,
  LayoutDashboard,
  Library,
  Skull,
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="flex min-h-screen">
      {/* ── Sidebar ──────────────────────────────────────────── */}
      <aside className="fixed top-0 left-0 z-40 flex h-screen w-64 flex-col border-r border-white/5 bg-surface-800/80 backdrop-blur-xl">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-3 border-b border-white/5 px-5 py-5"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-violet">
            <Skull size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white">
              Bug Archaeologist
            </h1>
            <p className="text-[10px] font-medium tracking-widest text-gray-500 uppercase">
              Git Intelligence
            </p>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          <NavItem
            to="/"
            icon={<Library size={18} />}
            label="Repositories"
            active={location.pathname === '/'}
          />
        </nav>

        {/* Footer */}
        <div className="border-t border-white/5 px-5 py-3">
          <p className="text-[10px] text-gray-600">v1.0.0 · Probabilistic Analysis</p>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────── */}
      <main className="ml-64 flex-1 min-h-screen">
        {children}
      </main>
    </div>
  );
}

/* ── Nav link component ──────────────────────────────────────── */
function NavItem({
  to,
  icon,
  label,
  active,
}: {
  to: string;
  icon: ReactNode;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
        active
          ? 'bg-accent/10 text-accent shadow-sm shadow-accent/5'
          : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
      }`}
    >
      {icon}
      {label}
    </Link>
  );
}

/* ── Sub-navigation for repo pages ───────────────────────────── */
export function RepoSubNav({ repoId, repoName }: { repoId: string; repoName: string }) {
  const location = useLocation();
  const base = `/repo/${repoId}`;

  const tabs = [
    { to: base, label: 'Dashboard', icon: <LayoutDashboard size={15} /> },
    { to: `${base}/bugs`, label: 'Bugs', icon: <Bug size={15} /> },
    { to: `${base}/commits`, label: 'Commits', icon: <GitCommitHorizontal size={15} /> },
  ];

  return (
    <div className="sticky top-0 z-30 border-b border-white/5 bg-surface-900/80 backdrop-blur-xl">
      <div className="px-8 pt-6 pb-0">
        <div className="flex items-center gap-2 mb-4">
          <Link to="/" className="text-gray-500 hover:text-gray-300 text-sm transition-colors">
            Repositories
          </Link>
          <span className="text-gray-600">/</span>
          <span className="text-white font-semibold text-sm">{repoName}</span>
        </div>
        <div className="flex gap-1">
          {tabs.map((tab) => {
            const active =
              tab.to === base
                ? location.pathname === base
                : location.pathname.startsWith(tab.to);
            return (
              <Link
                key={tab.to}
                to={tab.to}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all duration-200 ${
                  active
                    ? 'bg-surface-700/50 text-white border-b-2 border-accent'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                }`}
              >
                {tab.icon}
                {tab.label}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
