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

export function ProfileSkeleton() {
  return (
    <div className="flex flex-col items-center gap-4">
      <Skeleton className="w-32 h-32 rounded-full" />
      <Skeleton className="w-40 h-6" />
      <Skeleton className="w-24 h-4" />
      <Skeleton className="w-28 h-8 mt-2" />
    </div>
  );
}

export function PlaylistListSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-2">
          <Skeleton className="w-12 h-12 rounded" />
          <div className="flex-1">
            <Skeleton className="w-3/4 h-4 mb-2" />
            <Skeleton className="w-1/2 h-3" />
          </div>
        </div>
      ))}
    </div>
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
