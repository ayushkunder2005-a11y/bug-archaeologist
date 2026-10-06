import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  BarChart, Bar,
  LineChart, Line,
} from 'recharts';
import {
  GitCommitHorizontal, Bug, Code2, Users, Calendar, FileCode, Zap,
} from 'lucide-react';
import type { DashboardData } from '../types';
import { getDashboard, getRepository } from '../services/api';
import { RepoSubNav } from '../components/Layout';
import StatCard from '../components/StatCard';
import HealthGauge from '../components/HealthGauge';
import LoadingState from '../components/LoadingState';

const CHART_COLORS = {
  accent: '#3b82f6',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#ef4444',
  violet: '#8b5cf6',
  sky: '#0ea5e9',
};

const tooltipStyle = {
  contentStyle: {
    backgroundColor: '#1e293b',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '12px',
    fontSize: '12px',
    color: '#e2e8f0',
  },
  itemStyle: { color: '#e2e8f0' },
};

export default function Dashboard() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<DashboardData | null>(null);
  const [repoName, setRepoName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const [repo, dashboard] = await Promise.all([
          getRepository(id),
          getDashboard(id),
        ]);
        setRepoName(repo.name);
        setData(dashboard);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <LoadingState message="Loading dashboard..." />;
  if (error) {
    return (
      <div className="px-8 py-16 text-center">
        <p className="text-rose text-sm">{error}</p>
      </div>
    );
  }
  if (!data) return null;

  return (
    <div>
      <RepoSubNav repoId={id!} repoName={repoName} />

      <div className="px-8 py-6 space-y-6">
        {/* ── Stat Cards Row ──────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 stagger-children">
          <StatCard
            label="Total Commits"
            value={data.total_commits}
            icon={<GitCommitHorizontal size={18} />}
            color="accent"
            delay={0}
          />
          <StatCard
            label="Bugs Detected"
            value={data.total_bugs}
            icon={<Bug size={18} />}
            color="rose"
            delay={50}
          />
          <div className="glass-card-hover flex items-center justify-center p-5 animate-fade-in" style={{ animationDelay: '100ms' }}>
            <HealthGauge score={data.health_score} size={110} />
          </div>
          <StatCard
            label="Avg Complexity"
            value={data.avg_complexity.toFixed(1)}
            icon={<Zap size={18} />}
            color="amber"
            delay={150}
          />
          <StatCard
            label="Developers"
            value={data.total_developers}
            icon={<Users size={18} />}
            color="violet"
            subtitle={`${data.total_files} files analyzed`}
            delay={200}
          />
        </div>

        {/* ── Bug Timeline + Risk Distribution ─────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Bug Timeline */}
          <div className="lg:col-span-2 glass-card p-5 animate-fade-in" style={{ animationDelay: '250ms' }}>
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Calendar size={14} className="text-accent" />
              Bug Timeline
            </h3>
            {data.bug_timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={data.bug_timeline} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="introGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART_COLORS.rose} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={CHART_COLORS.rose} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="fixGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART_COLORS.emerald} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={CHART_COLORS.emerald} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Area type="monotone" dataKey="introductions" name="Introduced" stroke={CHART_COLORS.rose} fill="url(#introGrad)" strokeWidth={2} />
                  <Area type="monotone" dataKey="fixes" name="Fixed" stroke={CHART_COLORS.emerald} fill="url(#fixGrad)" strokeWidth={2} />
                  <Line type="monotone" dataKey="cumulative_open" name="Open Bugs" stroke={CHART_COLORS.amber} strokeWidth={2} dot={false} strokeDasharray="4 4" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-gray-500 py-12 text-center">No bug timeline data</p>
            )}
          </div>

          {/* Risk Distribution */}
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '300ms' }}>
            <h3 className="text-sm font-semibold text-white mb-4">Risk Distribution</h3>
            {data.risk_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={data.risk_distribution}
                    dataKey="count"
                    nameKey="label"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    strokeWidth={0}
                  >
                    {data.risk_distribution.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip {...tooltipStyle} />
                  <Legend
                    iconType="circle"
                    iconSize={6}
                    wrapperStyle={{ fontSize: '10px', color: '#9ca3af' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-gray-500 py-12 text-center">No risk data</p>
            )}
          </div>
        </div>

        {/* ── Top Problematic Files + Functions ────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Problematic Files */}
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '350ms' }}>
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <FileCode size={14} className="text-amber" />
              Most Bug-Prone Files
            </h3>
            {data.top_problematic_files.length > 0 ? (
              <ResponsiveContainer width="100%" height={Math.max(200, data.top_problematic_files.length * 32)}>
                <BarChart
                  data={data.top_problematic_files.slice(0, 10).map((f) => ({
                    name: f.file_path.split('/').pop() || f.file_path,
                    score: Math.round(f.bug_proneness_score),
                    fullPath: f.file_path,
                  }))}
                  layout="vertical"
                  margin={{ top: 0, right: 10, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#9ca3af' }} width={120} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Bar dataKey="score" name="Bug Score" fill={CHART_COLORS.rose} radius={[0, 4, 4, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-gray-500 py-12 text-center">No file analysis data</p>
            )}
          </div>

          {/* Bug-Prone Functions */}
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '400ms' }}>
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Code2 size={14} className="text-violet" />
              Bug-Prone Functions
            </h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {data.top_bug_prone_functions.length > 0 ? (
                data.top_bug_prone_functions.slice(0, 10).map((func, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg bg-surface-800/50 px-3 py-2.5"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-white truncate">
                        {func.name}
                        <span className="text-gray-600 text-xs ml-2">
                          :{func.line_number}
                        </span>
                      </p>
                      <p className="text-[10px] text-gray-500 truncate">{func.file_path}</p>
                    </div>
                    <div className="flex items-center gap-3 ml-3 shrink-0">
                      <div className="text-right">
                        <p className="text-xs font-semibold text-white">{func.complexity}</p>
                        <p className="text-[9px] text-gray-600">complexity</p>
                      </div>
                      <div
                        className="h-6 w-1 rounded-full"
                        style={{
                          backgroundColor: func.bug_proneness_score > 60
                            ? CHART_COLORS.rose
                            : func.bug_proneness_score > 30
                            ? CHART_COLORS.amber
                            : CHART_COLORS.emerald,
                        }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-gray-500 py-12 text-center">No function data</p>
              )}
            </div>
          </div>
        </div>

        {/* ── Developer Stats + Complexity Trends ─────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Developer Stats */}
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '450ms' }}>
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Users size={14} className="text-sky" />
              Developer Stats
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="pb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500">Developer</th>
                    <th className="pb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500 text-center">Commits</th>
                    <th className="pb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500 text-center">Fixes</th>
                    <th className="pb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500 text-center">Bug Intros</th>
                    <th className="pb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500 text-center">Avg Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.developer_stats.map((dev, i) => (
                    <tr key={i} className="hover:bg-white/[0.02]">
                      <td className="py-2.5">
                        <p className="text-sm font-medium text-white">{dev.name}</p>
                        <p className="text-[10px] text-gray-600">{dev.email}</p>
                      </td>
                      <td className="text-center text-sm text-gray-300">{dev.total_commits}</td>
                      <td className="text-center text-sm text-emerald">{dev.fix_commits}</td>
                      <td className="text-center text-sm text-rose">{dev.bug_introducing_commits}</td>
                      <td className="text-center">
                        <span
                          className={`text-sm font-semibold ${
                            dev.avg_risk_score > 50 ? 'text-rose' : dev.avg_risk_score > 25 ? 'text-amber' : 'text-emerald'
                          }`}
                        >
                          {dev.avg_risk_score}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Complexity Trends */}
          <div className="glass-card p-5 animate-fade-in" style={{ animationDelay: '500ms' }}>
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Zap size={14} className="text-amber" />
              Complexity Over Time
            </h3>
            {data.complexity_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data.complexity_trends} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Line type="monotone" dataKey="avg_complexity" name="Avg" stroke={CHART_COLORS.accent} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="max_complexity" name="Max" stroke={CHART_COLORS.rose} strokeWidth={2} dot={false} strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-gray-500 py-12 text-center">No complexity data</p>
            )}
          </div>
        </div>

        {/* Analysis date footer */}
        {data.analysis_date && (
          <p className="text-center text-xs text-gray-600 pb-4">
            Analysis completed on {new Date(data.analysis_date).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
}
