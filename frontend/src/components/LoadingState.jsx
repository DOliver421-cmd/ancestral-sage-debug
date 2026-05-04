import AppShell from "./AppShell";

/** Reusable, accessible loading state with a skeleton row pattern.
 *  Keeps every page's loading UX visually consistent. */
export function LoadingState({ label = "Loading…", inShell = true, rows = 3 }) {
  const inner = (
    <div className="px-10 py-10 max-w-6xl" role="status" aria-live="polite" data-testid="loading-state">
      <div className="overline text-copper">{label}</div>
      <div className="space-y-3 mt-6">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="h-12 bg-ink/5 animate-pulse" style={{ animationDelay: `${i * 80}ms` }} />
        ))}
      </div>
      <span className="sr-only">{label}</span>
    </div>
  );
  return inShell ? <AppShell>{inner}</AppShell> : inner;
}

export function EmptyState({ title, hint, icon: Icon, action }) {
  return (
    <div className="card-flat p-12 text-center" data-testid="empty-state">
      {Icon && <Icon className="w-12 h-12 text-ink/20 mx-auto" />}
      <div className="font-heading text-xl font-bold mt-4">{title}</div>
      {hint && <p className="text-sm text-ink/60 mt-2 max-w-sm mx-auto">{hint}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export default LoadingState;
