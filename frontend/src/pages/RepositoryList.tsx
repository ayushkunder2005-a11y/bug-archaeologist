import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  GitBranch,
  Clock,
  Loader2,
  Trash2,
  FolderGit2,
  Globe,
} from 'lucide-react';
import type { Repository } from '../types';
import { listRepositories, createRepository, deleteRepository, getRepositoryStatus } from '../services/api';
import EmptyState from '../components/EmptyState';

export default function RepositoryList() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formUrl, setFormUrl] = useState('');
  const [formLocal, setFormLocal] = useState('');
  const [formCommits, setFormCommits] = useState(500);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' | 'error' } | null>(null);

  const fetchRepos = async () => {
    try {
      const data = await listRepositories();
      setRepos(data.repositories);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(timer);
  }, [toast]);

  // Poll for analyzing repos (every 1.5s for fast status updates)
  useEffect(() => {
    const analyzing = repos.filter((r) => r.status === 'pending' || r.status === 'analyzing');
    if (analyzing.length === 0) return;

    const interval = setInterval(async () => {
      for (const repo of analyzing) {
        try {
          const status = await getRepositoryStatus(repo.id);
          if (status.status !== repo.status) {
            await fetchRepos();
            if (status.status === 'complete') {
              setToast({ message: `✅ Analysis complete for ${repo.name}!`, type: 'success' });
            } else if (status.status === 'error') {
              setToast({ message: `❌ Analysis error on ${repo.name}`, type: 'error' });
            }
            break;
          }
        } catch {
          // ignore
        }
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [repos]);

  const handleSubmit = async () => {
    if (!formUrl && !formLocal) return;
    setSubmitting(true);
    setError('');
    try {
      const newRepo = await createRepository(formUrl || undefined, formLocal || undefined, formCommits);
      setShowForm(false);
      setFormUrl('');
      setFormLocal('');
      // Optimistic update for instant UI response
      setRepos((prev) => [newRepo, ...prev.filter((r) => r.id !== newRepo.id)]);
      setToast({
        message: `🚀 Analysis launched for ${newRepo.name}! Mining history in background...`,
        type: 'info',
      });
      await fetchRepos();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteRepository(id);
      setRepos((r) => r.filter((x) => x.id !== id));
      setToast({ message: 'Repository deleted', type: 'info' });
    } catch (e: any) {
      setError(e.message);
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 75) return 'text-emerald';
    if (score >= 50) return 'text-amber';
    if (score >= 25) return 'text-orange-400';
    return 'text-rose';
  };

  const getStatusBadge = (status: string) => {
    const map: Record<string, { bg: string; text: string }> = {
      pending: { bg: 'bg-amber/10', text: 'text-amber' },
      analyzing: { bg: 'bg-accent/10', text: 'text-accent' },
      complete: { bg: 'bg-emerald/10', text: 'text-emerald' },
      error: { bg: 'bg-rose/10', text: 'text-rose' },
    };
    const c = map[status] || map.pending;
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${c.bg} ${c.text}`}
      >
        {(status === 'pending' || status === 'analyzing') && (
          <Loader2 size={10} className="animate-spin" />
        )}
        {status}
      </span>
    );
  };

  return (
    <div className="px-8 py-8 relative">
      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed top-6 right-8 z-50 flex items-center gap-3 rounded-xl border px-4 py-3 shadow-2xl backdrop-blur-xl animate-slide-in ${
            toast.type === 'success'
              ? 'border-emerald/30 bg-surface-800/90 text-emerald shadow-emerald/10'
              : toast.type === 'error'
              ? 'border-rose/30 bg-surface-800/90 text-rose shadow-rose/10'
              : 'border-accent/30 bg-surface-800/90 text-accent shadow-accent/10'
          }`}
        >
          <span className="text-sm font-medium">{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="text-xs opacity-60 hover:opacity-100 ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold text-white">Repositories</h1>
          <p className="text-sm text-gray-500 mt-1">
            Analyze Git repositories to uncover bug-introduction patterns
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:bg-accent-dim hover:shadow-lg hover:shadow-accent/20 active:scale-95"
        >
          <Plus size={16} />
          Add Repository
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 rounded-xl border border-rose/20 bg-rose/5 px-4 py-3 text-sm text-rose animate-fade-in">
          {error}
        </div>
      )}

      {/* Add Form */}
      {showForm && (
        <div className="glass-card p-6 mb-8 animate-fade-in">
          <h3 className="text-sm font-semibold text-white mb-4">Add Repository for Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">
                <Globe size={12} className="inline mr-1" />
                GitHub URL
              </label>
              <input
                type="text"
                value={formUrl}
                onChange={(e) => setFormUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="w-full rounded-lg border border-white/10 bg-surface-800 px-3 py-2 text-sm text-white placeholder-gray-600 outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">
                <FolderGit2 size={12} className="inline mr-1" />
                Local Path
              </label>
              <input
                type="text"
                value={formLocal}
                onChange={(e) => setFormLocal(e.target.value)}
                placeholder="C:\path\to\repo"
                className="w-full rounded-lg border border-white/10 bg-surface-800 px-3 py-2 text-sm text-white placeholder-gray-600 outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
              />
            </div>
          </div>
          <div className="flex items-end gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Max Commits</label>
              <input
                type="number"
                value={formCommits}
                onChange={(e) => setFormCommits(Number(e.target.value))}
                min={10}
                max={5000}
                className="w-28 rounded-lg border border-white/10 bg-surface-800 px-3 py-2 text-sm text-white outline-none transition-colors focus:border-accent/50"
              />
            </div>
            <button
              onClick={handleSubmit}
              disabled={submitting || (!formUrl && !formLocal)}
              className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-white transition-all hover:bg-accent-dim disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {submitting && <Loader2 size={14} className="animate-spin" />}
              Start Analysis
            </button>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-1 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass-card p-6">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 skeleton rounded-xl" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-48 skeleton" />
                  <div className="h-3 w-32 skeleton" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty */}
      {!loading && repos.length === 0 && (
        <EmptyState
          icon={<GitBranch size={28} />}
          title="No repositories yet"
          description="Add a Git repository URL or local path to begin bug archaeology analysis."
          action={
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 rounded-lg bg-accent/10 px-4 py-2 text-sm font-medium text-accent transition-colors hover:bg-accent/20"
            >
              <Plus size={14} />
              Add your first repository
            </button>
          }
        />
      )}

      {/* Repository cards */}
      {!loading && repos.length > 0 && (
        <div className="grid grid-cols-1 gap-4 stagger-children">
          {repos.map((repo) => (
            <div key={repo.id} className="glass-card-hover group">
              <div className="flex items-center p-5">
                {/* Icon */}
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent/20 to-violet/10 mr-4">
                  <GitBranch size={20} className="text-accent" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    {repo.status === 'complete' ? (
                      <Link
                        to={`/repo/${repo.id}`}
                        className="text-base font-semibold text-white hover:text-accent transition-colors truncate"
                      >
                        {repo.name}
                      </Link>
                    ) : (
                      <span className="text-base font-semibold text-white truncate">
                        {repo.name}
                      </span>
                    )}
                    {getStatusBadge(repo.status)}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    {repo.primary_language && (
                      <span className="flex items-center gap-1">
                        <span className="h-2 w-2 rounded-full bg-accent" />
                        {repo.primary_language}
                      </span>
                    )}
                    {repo.url && (
                      <span className="truncate max-w-xs">{repo.url}</span>
                    )}
                    {repo.analyzed_at && (
                      <span className="flex items-center gap-1">
                        <Clock size={10} />
                        {new Date(repo.analyzed_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Stats */}
                {repo.status === 'complete' && (
                  <div className="hidden md:flex items-center gap-6 mr-4">
                    <div className="text-center">
                      <p className="text-lg font-bold text-white">{repo.total_commits}</p>
                      <p className="text-[10px] text-gray-500 uppercase tracking-wider">Commits</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold text-rose">{repo.total_bugs_detected}</p>
                      <p className="text-[10px] text-gray-500 uppercase tracking-wider">Bugs</p>
                    </div>
                    <div className="text-center">
                      <p className={`text-lg font-bold ${getHealthColor(repo.health_score)}`}>
                        {Math.round(repo.health_score)}
                      </p>
                      <p className="text-[10px] text-gray-500 uppercase tracking-wider">Health</p>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {repo.status === 'complete' && (
                    <Link
                      to={`/repo/${repo.id}`}
                      className="rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/20"
                    >
                      View Dashboard
                    </Link>
                  )}
                  <button
                    onClick={() => handleDelete(repo.id)}
                    className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-rose/10 hover:text-rose opacity-0 group-hover:opacity-100"
                    title="Delete repository"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {/* Error message */}
              {repo.error_message && (
                <div className="border-t border-white/5 px-5 py-3 text-xs text-rose">
                  {repo.error_message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
