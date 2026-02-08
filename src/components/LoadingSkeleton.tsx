export function TableSkeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="flex gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex-1 h-10 bg-slate-200 dark:bg-slate-800 rounded"></div>
        ))}
      </div>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-3">
          {[1, 2, 3, 4].map((j) => (
            <div key={j} className="flex-1 h-8 bg-slate-100 dark:bg-slate-900 rounded"></div>
          ))}
        </div>
      ))}
    </div>
  );
}

export function DatasetSummarySkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
      <div className="space-y-2">
        <div className="h-4 bg-slate-100 dark:bg-slate-900 rounded w-full"></div>
        <div className="h-4 bg-slate-100 dark:bg-slate-900 rounded w-5/6"></div>
        <div className="h-4 bg-slate-100 dark:bg-slate-900 rounded w-4/6"></div>
      </div>
      <div className="grid grid-cols-2 gap-3 mt-4">
        <div className="h-20 bg-slate-100 dark:bg-slate-900 rounded-lg"></div>
        <div className="h-20 bg-slate-100 dark:bg-slate-900 rounded-lg"></div>
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="animate-pulse p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-slate-200 dark:bg-slate-800 rounded-lg"></div>
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
          <div className="h-3 bg-slate-100 dark:bg-slate-900 rounded w-1/2"></div>
        </div>
      </div>
    </div>
  );
}

export function ListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}
