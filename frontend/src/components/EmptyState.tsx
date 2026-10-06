import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-700/50 text-gray-500 mb-4">
        {icon || <Inbox size={28} />}
      </div>
      <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 max-w-sm text-center mb-4">{description}</p>
      )}
      {action}
    </div>
  );
}
