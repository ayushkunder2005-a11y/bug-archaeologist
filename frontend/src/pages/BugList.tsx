import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowUpDown, Clock, FileCode, User } from 'lucide-react';
import type { Bug } from '../types';
import { getBugs, getRepository } from '../services/api';
import { RepoSubNav } from '../components/Layout';
import SeverityBadge from '../components/SeverityBadge';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';

type SortField = 'severity' | 'time_to_fix_days' | 'introduction_date' | 'complexity_after';
type SortDir = 'asc' | 'desc';

const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };

export default function BugList() {
  const { id } = useParams<{ id: string }>();
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [repoName, setRepoName] = useState('');
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<SortField>('severity');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const [repo, bugData] = await Promise.all([
          getRepository(id),
          getBugs(id),
        ]);
        setRepoName(repo.name);
        setBugs(bugData.bugs);
      } catch {
        // handled by empty state
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const filtered = bugs.filter(
    (b) => filterSeverity === 'all' || b.severity === filterSeverity,
  );

  const sorted = [...filtered].sort((a, b) => {
    let cmp = 0;
    if (sortField === 'severity') {
      cmp = severityOrder[a.severity] - severityOrder[b.severity];
    } else if (sortField === 'time_to_fix_days') {
      cmp = a.time_to_fix_days - b.time_to_fix_days;
    } else if (sortField === 'introduction_date') {
      cmp = new Date(a.introduction_date).getTime() - new Date(b.introduction_date).getTime();
    } else if (sortField === 'complexity_after') {
      cmp = a.complexity_after - b.complexity_after;
    }
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => toggleSort(field)}
      className={`flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider transition-colors ${
        sortField === field ? 'text-accent' : 'text-gray-500 hover:text-gray-300'
      }`}
    >
      {label}
      <ArrowUpDown size={10} />
    </button>
  );

  if (loading) return <LoadingState message="Loading bugs..." />;

  return (
    <div>
      <RepoSubNav repoId={id!} repoName={repoName} />

      <div className="px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 animate-fade-in">
          <div>
            <h2 className="text-lg font-bold text-white">Detected Bugs</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {bugs.length} bugs found via SZZ analysis
            </p>
          </div>

          {/* Severity filter */}
          <div className="flex gap-1.5">
            {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition-all ${
                  filterSeverity === sev
                    ? 'bg-accent/10 text-accent'
                    : 'text-gray-500 hover:bg-white/5 hover:text-gray-300'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {sorted.length === 0 ? (
          <EmptyState
            title="No bugs found"
            description={filterSeverity !== 'all' ? 'Try changing the severity filter.' : 'Great news — no bugs detected!'}
          />
        ) : (
          <div className="glass-card overflow-hidden animate-fade-in">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/5 bg-surface-800/50">
                  <th className="px-5 py-3"><SortHeader field="severity" label="Severity" /></th>
                  <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">Bug</th>
                  <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">Files</th>
                  <th className="px-5 py-3"><SortHeader field="introduction_date" label="Introduced" /></th>
                  <th className="px-5 py-3"><SortHeader field="time_to_fix_days" label="Time to Fix" /></th>
                  <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">Authors</th>
                  <th className="px-5 py-3"><SortHeader field="complexity_after" label="Complexity" /></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {sorted.map((bug) => (
                  <tr key={bug.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-5 py-3">
                      <SeverityBadge severity={bug.severity} />
                    </td>
                    <td className="px-5 py-3 max-w-xs">
                      <Link
                        to={`/repo/${id}/bugs/${bug.id}`}
                        className="text-sm font-medium text-white hover:text-accent transition-colors line-clamp-2"
                      >
                        {bug.title}
                      </Link>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1 text-xs text-gray-400">
                        <FileCode size={12} />
                        {bug.affected_files?.length || 0}
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock size={11} />
                        {new Date(bug.introduction_date).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`text-xs font-semibold ${
                          bug.time_to_fix_days < 7
                            ? 'text-emerald'
                            : bug.time_to_fix_days < 30
                            ? 'text-amber'
                            : 'text-rose'
                        }`}
                      >
                        {bug.time_to_fix_days < 1
                          ? '< 1 day'
                          : `${Math.round(bug.time_to_fix_days)} days`}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <div className="text-xs">
                        <p className="text-rose flex items-center gap-1">
                          <User size={10} /> {bug.introducing_author || '—'}
                        </p>
                        <p className="text-emerald flex items-center gap-1 mt-0.5">
                          <User size={10} /> {bug.fix_author || '—'}
                        </p>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <div className="text-xs">
                        <span className="text-gray-500">{bug.complexity_before.toFixed(1)}</span>
                        <span className="text-gray-600 mx-1">→</span>
                        <span
                          className={
                            bug.complexity_after > bug.complexity_before
                              ? 'text-rose font-semibold'
                              : 'text-emerald'
                          }
                        >
                          {bug.complexity_after.toFixed(1)}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
