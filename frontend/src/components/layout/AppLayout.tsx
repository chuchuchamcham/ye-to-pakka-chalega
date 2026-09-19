import type { ReactNode } from "react";
import { authApi, type SessionUser } from "../../api/auth";
import { Sidebar } from "./Sidebar";

export function AppLayout({
  children,
  user,
  onSignedOut,
}: {
  children: ReactNode;
  user?: SessionUser | null;
  onSignedOut?: () => void;
}) {
  return (
    <div className="grid min-h-screen grid-cols-[248px_1fr] max-[1366px]:grid-cols-[220px_1fr]">
      <Sidebar user={user} onSignedOut={onSignedOut} />
      <div className="flex min-w-0 flex-col">{children}</div>
    </div>
  );
}

/** Who is signed in, and how to stop being signed in. */
export function SessionFooter({
  user,
  onSignedOut,
}: {
  user?: SessionUser | null;
  onSignedOut?: () => void;
}) {
  if (!user) return null;
  return (
    <div className="mx-5 mt-4 border-t border-border-1 pt-4">
      <div className="truncate text-[12px] font-semibold text-text-primary">{user.username}</div>
      <div className="mb-2 text-[10.5px] tracking-wide text-text-tertiary">{user.role}</div>
      <button
        onClick={() => {
          void authApi.logout().finally(() => onSignedOut?.());
        }}
        className="w-full rounded border border-border-2 py-1.5 text-[11.5px] text-text-secondary hover:bg-bg-3 hover:text-text-primary"
      >
        Sign out
      </button>
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="sticky top-0 z-10 flex h-[60px] shrink-0 items-center justify-between border-b border-border-1 bg-bg-1 px-6">
      <div className="flex flex-col gap-0.5">
        <h1 className="text-[15px] font-semibold text-text-primary">{title}</h1>
        {subtitle && <p className="text-[11px] text-text-tertiary">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}

export function PageBody({ children, narrow }: { children: ReactNode; narrow?: boolean }) {
  return <div className={`flex-1 p-6 max-[1366px]:p-5 ${narrow ? "max-w-[1040px]" : ""}`}>{children}</div>;
}
