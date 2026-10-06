import { useEffect, useState } from 'react';

interface HealthGaugeProps {
  score: number; // 0–100
  size?: number;
  label?: string;
}

export default function HealthGauge({ score, size = 140, label = 'Health Score' }: HealthGaugeProps) {
  const [offset, setOffset] = useState(283);

  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const targetOffset = circumference - (clampedScore / 100) * circumference;

  useEffect(() => {
    const timer = setTimeout(() => setOffset(targetOffset), 100);
    return () => clearTimeout(timer);
  }, [targetOffset]);

  const getColor = (s: number) => {
    if (s >= 75) return { stroke: '#10b981', text: 'text-emerald', label: 'Excellent' };
    if (s >= 50) return { stroke: '#f59e0b', text: 'text-amber', label: 'Fair' };
    if (s >= 25) return { stroke: '#f97316', text: 'text-orange-400', label: 'Poor' };
    return { stroke: '#ef4444', text: 'text-rose', label: 'Critical' };
  };

  const color = getColor(clampedScore);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          viewBox="0 0 100 100"
          className="transform -rotate-90"
          style={{ width: size, height: size }}
        >
          {/* Background ring */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="8"
          />
          {/* Score ring */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke={color.stroke}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="gauge-ring"
            style={{ filter: `drop-shadow(0 0 6px ${color.stroke}40)` }}
          />
        </svg>
        {/* Score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${color.text}`}>
            {Math.round(clampedScore)}
          </span>
          <span className="text-[10px] font-medium text-gray-500 uppercase tracking-wider">
            {color.label}
          </span>
        </div>
      </div>
      <p className="text-xs font-medium text-gray-500">{label}</p>
    </div>
  );
}
