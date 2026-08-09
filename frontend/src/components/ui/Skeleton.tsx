interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-spotify-light-gray rounded ${className}`}
    />
  );
}

export function ResultSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="w-3/4 h-6" />
      <Skeleton className="w-full h-4" />
      <Skeleton className="w-full h-4" />
      <div className="space-y-2 mt-6">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="w-6 h-4" />
            <Skeleton className="w-10 h-10 rounded" />
            <div className="flex-1">
              <Skeleton className="w-1/2 h-4 mb-1" />
              <Skeleton className="w-1/3 h-3" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
