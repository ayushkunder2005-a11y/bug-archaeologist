import type { ReactNode } from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  color?: string;
  subtitle?: string;
  delay?: number;
}

export default function StatCard({
  label,
  value,
  icon,
  color = 'accent',
  subtitle,
  delay = 0,
}: StatCardProps) {
  const colorMap: Record<string, string> = {
    accent: 'from-accent/20 to-accent/5 text-accent',
    emerald: 'from-emerald/20 to-emerald/5 text-emerald',
    amber: 'from-amber/20 to-amber/5 text-amber',
    rose: 'from-rose/20 to-rose/5 text-rose',
    violet: 'from-violet/20 to-violet/5 text-violet',
    sky: 'from-sky/20 to-sky/5 text-sky',
  };

  const iconBg = colorMap[color] || colorMap.accent;

  return (
    <div
      className="glass-card-hover p-5 animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">
            {label}
          </p>
          <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
          {subtitle && (
            <p className="mt-1 text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${iconBg}`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}
