import { useState } from "react";
import { Loader2, ShieldCheck } from "lucide-react";
import { ApiError } from "../api/client";
import { authApi, type SessionState } from "../api/auth";

/**
 * Sign-in, and first-run administrator creation.
 *
 * The two share a screen because they are the same moment from the operator's
 * point of view: this system needs to know who you are. Which one is shown
 * depends on whether any account exists yet, so a fresh install cannot be left
 * accidentally open - there is no state in which the API is reachable without
 * an account.
 */
export function Login({ session, onSignedIn }: { session: SessionState; onSignedIn: () => void }) {
  const firstRun = !session.configured;
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tooShort = firstRun && password.length > 0 && password.length < 8;
  const mismatch = firstRun && confirm.length > 0 && confirm !== password;
  const canSubmit =
    username.trim().length > 0 &&
    password.length > 0 &&
    (!firstRun || (password.length >= 8 && confirm === password));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || busy) return;
    setBusy(true);
    setError(null);
    try {
      if (firstRun) await authApi.bootstrap(username.trim(), password);
      else await authApi.login(username.trim(), password);
      onSignedIn();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-0 px-4">
      <form onSubmit={submit} className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="mb-2 flex items-center justify-center gap-2 text-lg font-bold tracking-wide text-text-primary">
            <span className="h-2 w-2 rounded-full bg-accent-blue shadow-[0_0_8px_var(--color-accent-blue)]" />
            DRISHTI
          </div>
          <div className="text-[11px] tracking-[1.5px] text-text-tertiary">AI VIDEO INTELLIGENCE</div>
        </div>

        <div className="rounded-lg border border-border-1 bg-bg-2 p-5">
          <h1 className="mb-1 text-[15px] font-bold text-text-primary">
            {firstRun ? "Create administrator" : "Sign in"}
          </h1>
          <p className="mb-4 text-[12px] leading-relaxed text-text-tertiary">
            {firstRun
              ? "No accounts exist yet. This first account has full control, including cameras, evidence and users."
              : "Camera feeds, evidence and the audit trail require a signed-in account."}
          </p>

          <label className="mb-1 block text-[11.5px] font-semibold text-text-secondary">Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            autoComplete="username"
            className="mb-3 w-full rounded border border-border-2 bg-bg-3 px-3 py-2 text-[13px] text-text-primary focus:border-accent-blue focus:outline-none"
          />

          <label className="mb-1 block text-[11.5px] font-semibold text-text-secondary">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={firstRun ? "new-password" : "current-password"}
            className="w-full rounded border border-border-2 bg-bg-3 px-3 py-2 text-[13px] text-text-primary focus:border-accent-blue focus:outline-none"
          />
          {tooShort && (
            <div className="mt-1 text-[11px] text-accent-amber">At least 8 characters.</div>
          )}

          {firstRun && (
            <>
              <label className="mb-1 mt-3 block text-[11.5px] font-semibold text-text-secondary">
                Confirm password
              </label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
                className="w-full rounded border border-border-2 bg-bg-3 px-3 py-2 text-[13px] text-text-primary focus:border-accent-blue focus:outline-none"
              />
              {mismatch && (
                <div className="mt-1 text-[11px] text-accent-red">Passwords do not match.</div>
              )}
            </>
          )}

          {error && (
            <div className="mt-3 rounded border border-accent-red/35 bg-accent-red/10 px-3 py-2 text-[12px] text-accent-red">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!canSubmit || busy}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded bg-accent-blue py-2.5 text-[13px] font-semibold text-[#051020] disabled:opacity-40"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <ShieldCheck size={14} />}
            {firstRun ? "Create administrator" : "Sign in"}
          </button>
        </div>
      </form>
    </div>
  );
}
