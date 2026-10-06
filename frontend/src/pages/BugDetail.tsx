import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, ArrowRight, Clock, FileCode, GitCommitHorizontal, User, Zap, AlertTriangle,
} from 'lucide-react';
import type { Bug } from '../types';
import { getBugDetail, getRepository } from '../services/api';
import { RepoSubNav } from '../components/Layout';
import SeverityBadge from '../components/SeverityBadge';
import LoadingState from '../components/LoadingState';

export default function BugDetail() {
  const { id, bugId } = useParams<{ id: string; bugId: string }>();
  const [bug, setBug] = useState<Bug | null>(null);
  const [repoName, setRepoName] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id || !bugId) return;
    (async () => {
      try {
        const [repo, bugData] = await Promise.all([
          getRepository(id),
          getBugDetail(id, bugId),
        ]);
        setRepoName(repo.name);
        setBug(bugData);
      } catch {
        // handled below
      } finally {
        setLoading(false);
      }
    })();
  }, [id, bugId]);

  if (loading) return <LoadingState message="Loading bug details..." />;
  if (!bug) {
    return (
      <div className="px-8 py-16 text-center">
        <p className="text-rose text-sm">Bug not found</p>
      </div>
    );
  }

  const complexityIncreased = bug.complexity_after > bug.complexity_before;
  const ttfLabel =
    bug.time_to_fix_days < 1
      ? '< 1 day'
      : `${Math.round(bug.time_to_fix_days)} days`;

  return (
    <div>
      <RepoSubNav repoId={id!} repoName={repoName} />

      <div className="px-8 py-6 max-w-4xl">
        {/* Back link */}
        <Link
          to={`/repo/${id}/bugs`}
          className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-accent transition-colors mb-4"
        >
          <ArrowLeft size={12} />
          Back to bugs
        </Link>

        {/* Title */}
        <div className="flex items-start gap-4 mb-6 animate-fade-in">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-rose/20 to-rose/5">
            <AlertTriangle size={20} className="text-rose" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white mb-2">{bug.title}</h1>
            <div className="flex items-center gap-3">
              <SeverityBadge severity={bug.severity} size="md" />
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Clock size={11} /> Fixed in {ttfLabel}
              </span>
            </div>
          </div>
        </div>

        {/* ── Timeline card ────────────────────────────────────── */}
        <div className="glass-card p-5 mb-4 animate-fade-in" style={{ animationDelay: '100ms' }}>
          <h3 className="text-sm font-semibold text-white mb-4">Bug Lifecycle</h3>
          <div className="flex items-center gap-4">
            {/* Introducing commit */}
            <div className="flex-1 rounded-xl bg-rose/5 border border-rose/10 p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-rose mb-2">
                Introduced
              </p>
              <div className="flex items-center gap-2 mb-1">
                <GitCommitHorizontal size={12} className="text-gray-500" />
                <code className="text-xs text-white font-mono">
                  {bug.introducing_commit_hash.slice(0, 8)}
                </code>
              </div>
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <User size={10} /> {bug.introducing_author || 'Unknown'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(bug.introduction_date).toLocaleDateString()}
              </p>
            </div>

            {/* Arrow */}
            <div className="flex flex-col items-center">
              <ArrowRight size={20} className="text-gray-600" />
              <span className="text-[9px] text-gray-600 mt-1">{ttfLabel}</span>
            </div>

            {/* Fix commit */}
            <div className="flex-1 rounded-xl bg-emerald/5 border border-emerald/10 p-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald mb-2">
                Fixed
              </p>
              <div className="flex items-center gap-2 mb-1">
                <GitCommitHorizontal size={12} className="text-gray-500" />
                <code className="text-xs text-white font-mono">
                  {bug.fix_commit_hash.slice(0, 8)}
                </code>
              </div>
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <User size={10} /> {bug.fix_author || 'Unknown'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(bug.fix_date).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* ── Details grid ─────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Affected files */}
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '200ms' }}>
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <FileCode size={14} className="text-amber" />
              Affected Files
            </h3>
            {bug.affected_files && bug.affected_files.length > 0 ? (
              <ul className="space-y-1.5">
                {bug.affected_files.map((f, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-2 rounded-lg bg-surface-800/50 px-3 py-2"
                  >
                    <FileCode size={12} className="text-gray-500 shrink-0" />
                    <span className="text-xs text-gray-300 truncate font-mono">{f}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-500">No file data available</p>
            )}
          </div>

          {/* Complexity */}
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '250ms' }}>
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Zap size={14} className="text-amber" />
              Complexity Impact
            </h3>
            <div className="flex items-center justify-center gap-6 py-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-300">{bug.complexity_before.toFixed(1)}</p>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">Before</p>
              </div>
              <ArrowRight
                size={20}
                className={complexityIncreased ? 'text-rose' : 'text-emerald'}
              />
              <div className="text-center">
                <p
                  className={`text-2xl font-bold ${
                    complexityIncreased ? 'text-rose' : 'text-emerald'
                  }`}
                >
                  {bug.complexity_after.toFixed(1)}
                </p>
                <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-1">After</p>
              </div>
            </div>
            {complexityIncreased && (
              <p className="text-center text-xs text-rose/70">
                Complexity increased by{' '}
                {(bug.complexity_after - bug.complexity_before).toFixed(1)}
              </p>
            )}

            {/* Affected functions */}
            {bug.affected_functions && bug.affected_functions.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-500 mb-2">
                  Affected Functions
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {bug.affected_functions.map((fn, i) => (
                    <span
                      key={i}
                      className="rounded-md bg-violet/10 px-2 py-0.5 text-[10px] font-mono text-violet"
                    >
                      {fn}()
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Explanation ───────────────────────────────────────── */}
        {bug.explanation && (
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '300ms' }}>
            <h3 className="text-sm font-semibold text-white mb-3">Analysis Explanation</h3>
            <p className="text-sm leading-relaxed text-gray-400">{bug.explanation}</p>
          </div>
        )}

        {/* Related commits */}
        {bug.related_commit_hashes && bug.related_commit_hashes.length > 0 && (
          <div className="glass-card p-5 mt-4 animate-fade-in" style={{ animationDelay: '350ms' }}>
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <GitCommitHorizontal size={14} className="text-accent" />
              Related Commits
            </h3>
            <div className="flex flex-wrap gap-2">
              {bug.related_commit_hashes.map((hash, i) => (
                <code
                  key={i}
                  className="rounded-md bg-surface-800/50 px-2.5 py-1 text-xs font-mono text-gray-400"
                >
                  {hash.slice(0, 8)}
                </code>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
