interface SeverityBadgeProps {
  severity: 'low' | 'medium' | 'high' | 'critical';
  size?: 'sm' | 'md';
}

const config = {
  low: {
    bg: 'bg-emerald/10',
    text: 'text-emerald',
    border: 'border-emerald/20',
    dot: 'bg-emerald',
  },
  medium: {
    bg: 'bg-amber/10',
    text: 'text-amber',
    border: 'border-amber/20',
    dot: 'bg-amber',
  },
  high: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-400',
    border: 'border-orange-500/20',
    dot: 'bg-orange-400',
  },
  critical: {
    bg: 'bg-rose/10',
    text: 'text-rose',
    border: 'border-rose/20',
    dot: 'bg-rose',
  },
};

export default function SeverityBadge({ severity, size = 'sm' }: SeverityBadgeProps) {
  const c = config[severity];
  const sizing = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold uppercase tracking-wider ${c.bg} ${c.text} ${c.border} ${sizing}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {severity}
    </span>
  );
}
