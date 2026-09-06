// Universal Navigation & Breadcrumb Bar (Zero Dead Ends Pattern)

export function NavigationBar({
  breadcrumbs,
  onBack,
  backLabel = "← Return to Previous Step",
}: {
  breadcrumbs: { label: string; onClick?: () => void; active?: boolean }[];
  onBack?: () => void;
  backLabel?: string;
}) {
  return (
    <nav className="nav-breadcrumb-bar" aria-label="Breadcrumb and page navigation">
      <div className="nav-breadcrumb-inner">
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {onBack && (
            <button
              type="button"
              className="nav-back-btn"
              onClick={onBack}
              title={backLabel}
            >
              {backLabel}
            </button>
          )}

          <div className="breadcrumbs">
            {breadcrumbs.map((b, i) => (
              <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
                {i > 0 && <span>/</span>}
                {b.onClick ? (
                  <button
                    type="button"
                    className="btn ghost"
                    style={{ padding: "0 0.2rem", fontSize: "0.8rem", textDecoration: "underline", color: "var(--gov-blue)" }}
                    onClick={b.onClick}
                  >
                    {b.label}
                  </button>
                ) : (
                  <span className={b.active ? "current" : ""}>{b.label}</span>
                )}
              </span>
            ))}
          </div>
        </div>

      </div>
    </nav>
  );
}
