export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-500">
      <span
        aria-hidden
        className="h-5 w-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent"
      />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  message,
  action,
}: {
  title: string;
  message?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center gap-2 px-6 py-12 text-center">
      <svg viewBox="0 0 24 24" className="h-10 w-10 text-ink-300" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
        <path d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125M21 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <h3 className="text-base font-semibold text-ink-800">{title}</h3>
      {message && <p className="max-w-sm text-sm text-ink-500">{message}</p>}
      {action}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="card border-red-200 bg-red-50 px-6 py-8 text-center">
      <h3 className="text-base font-semibold text-red-800">Something went wrong</h3>
      <p className="mx-auto mt-1 max-w-md text-sm text-red-600">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-100"
        >
          Try again
        </button>
      )}
    </div>
  );
}
