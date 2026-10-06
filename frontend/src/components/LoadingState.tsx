export default function LoadingState({ message = 'Analyzing repository...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
      {/* Animated skeleton */}
      <div className="relative mb-8">
        <div className="h-16 w-16 rounded-2xl skeleton" />
        <div className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-accent animate-pulse-glow" />
      </div>

      <p className="text-sm font-medium text-gray-400 mb-6">{message}</p>

      {/* Skeleton cards */}
      <div className="grid w-full max-w-2xl grid-cols-2 gap-4 px-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="glass-card p-5 space-y-3"
            style={{ animationDelay: `${i * 150}ms` }}
          >
            <div className="h-3 w-20 skeleton" />
            <div className="h-6 w-16 skeleton" />
            <div className="h-2 w-full skeleton" />
          </div>
        ))}
      </div>
    </div>
  );
}
