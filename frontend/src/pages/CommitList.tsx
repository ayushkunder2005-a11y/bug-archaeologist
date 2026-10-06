import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  FileCode,
  AlertTriangle,
  CheckCircle2,
  Shield,
} from 'lucide-react';
import type { Commit } from '../types';
import { getCommits, getRepository } from '../services/api';
import { RepoSubNav } from '../components/Layout';
import LoadingState from '../components/LoadingState';

export default function CommitList() {
  const { id } = useParams<{ id: string }>();
  const [commits, setCommits] = useState<Commit[]>([]);
  const [repoName, setRepoName] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 50;

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const [repo, data] = await Promise.all([
          getRepository(id),
          getCommits(id, page, perPage),
        ]);
        setRepoName(repo.name);
        setCommits(data.commits);
        setTotal(data.total);
      } catch {
        // handled by empty state
      } finally {
        setLoading(false);
      }
    })();
  }, [id, page]);

  const totalPages = Math.ceil(total / perPage);

  const getRiskColor = (score: number) => {
    if (score >= 75) return 'bg-rose text-white';
    if (score >= 50) return 'bg-orange-500 text-white';
    if (score >= 25) return 'bg-amber text-black';
    return 'bg-surface-600/50 text-gray-400';
  };

  const getRiskBarWidth = (score: number) => `${Math.min(100, score)}%`;
  const getRiskBarColor = (score: number) => {
    if (score >= 75) return 'bg-rose';
    if (score >= 50) return 'bg-orange-500';
    if (score >= 25) return 'bg-amber';
    return 'bg-emerald';
  };

  if (loading) return <LoadingState message="Loading commits..." />;

  return (
    <div>
      <RepoSubNav repoId={id!} repoName={repoName} />

      <div className="px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 animate-fade-in">
          <div>
            <h2 className="text-lg font-bold text-white">Commit History</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {total} commits analyzed · Page {page} of {totalPages}
            </p>
          </div>
        </div>

        {/* Table */}
        <div className="glass-card overflow-hidden animate-fade-in">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5 bg-surface-800/50">
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                  Commit
                </th>
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                  Message
                </th>
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                  Author
                </th>
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                  Date
                </th>
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                  Changes
                </th>
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500 w-40">
                  Risk Score
                </th>
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                  Flags
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {commits.map((c) => (
                <tr
                  key={c.id}
                  className={`hover:bg-white/[0.02] transition-colors ${
                    c.is_bug_introducing ? 'bg-rose/[0.02]' : ''
                  }`}
                >
                  {/* Hash */}
                  <td className="px-5 py-3">
                    <code className="text-xs font-mono text-accent">{c.short_hash}</code>
                  </td>

                  {/* Message */}
                  <td className="px-5 py-3 max-w-sm">
                    <p className="text-sm text-gray-300 truncate" title={c.message}>
                      {c.message.split('\n')[0]}
                    </p>
                  </td>

                  {/* Author */}
                  <td className="px-5 py-3">
                    <p className="text-xs text-gray-400">{c.author_name}</p>
                  </td>

                  {/* Date */}
                  <td className="px-5 py-3">
                    <span className="text-xs text-gray-500">
                      {new Date(c.authored_date).toLocaleDateString()}
                    </span>
                  </td>

                  {/* Changes */}
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2 text-xs">
                      <FileCode size={11} className="text-gray-500" />
                      <span className="text-gray-400">{c.files_changed}</span>
                      <span className="text-emerald">+{c.insertions}</span>
                      <span className="text-rose">-{c.deletions}</span>
                    </div>
                  </td>

                  {/* Risk Score */}
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 rounded-full bg-surface-600/30 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${getRiskBarColor(c.bug_intro_score)}`}
                          style={{ width: getRiskBarWidth(c.bug_intro_score) }}
                        />
                      </div>
                      <span
                        className={`rounded-md px-1.5 py-0.5 text-[10px] font-bold ${getRiskColor(c.bug_intro_score)}`}
                      >
                        {Math.round(c.bug_intro_score)}
                      </span>
                    </div>
                  </td>

                  {/* Flags */}
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-1.5">
                      {c.is_bug_introducing && (
                        <span className="flex items-center gap-1 rounded-full bg-rose/10 px-2 py-0.5 text-[9px] font-semibold text-rose uppercase">
                          <AlertTriangle size={9} />
                          Bug
                        </span>
                      )}
                      {c.is_fix_commit && (
                        <span className="flex items-center gap-1 rounded-full bg-emerald/10 px-2 py-0.5 text-[9px] font-semibold text-emerald uppercase">
                          <CheckCircle2 size={9} />
                          Fix
                        </span>
                      )}
                      {!c.is_bug_introducing && !c.is_fix_commit && (
                        <span className="flex items-center gap-1 rounded-full bg-surface-600/20 px-2 py-0.5 text-[9px] text-gray-600">
                          <Shield size={9} />
                          Clean
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6 animate-fade-in">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="flex items-center gap-1 rounded-lg bg-surface-700/50 px-3 py-2 text-xs font-medium text-gray-400 transition-colors hover:bg-surface-600/50 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={14} />
              Previous
            </button>
            <div className="flex gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum =
                  totalPages <= 5
                    ? i + 1
                    : page <= 3
                    ? i + 1
                    : page >= totalPages - 2
                    ? totalPages - 4 + i
                    : page - 2 + i;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`h-8 w-8 rounded-lg text-xs font-medium transition-colors ${
                      page === pageNum
                        ? 'bg-accent text-white'
                        : 'bg-surface-700/50 text-gray-400 hover:bg-surface-600/50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="flex items-center gap-1 rounded-lg bg-surface-700/50 px-3 py-2 text-xs font-medium text-gray-400 transition-colors hover:bg-surface-600/50 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
