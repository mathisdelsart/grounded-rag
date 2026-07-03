"use client";

import { useState } from "react";
import { login, me, register, type AuthUser, type ConnectionConfig } from "@/lib/api";
import { Button } from "@/components/Button";
import { Card, CardBody } from "@/components/Card";
import { TextField } from "@/components/TextField";
import { BrandMark } from "@/components/Logo";
import { useToast } from "@/components/Toast";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/cn";

interface AuthCardProps {
  config: ConnectionConfig;
  /** Called on a successful sign-in with the token and the resolved identity. */
  onLogin: (token: string, email: string, displayName?: string | null) => void;
  /** Optional hook fired after a successful sign-in (e.g. to close a modal). */
  onSuccess?: () => void;
  className?: string;
}

type Mode = "login" | "register";

/**
 * Shared, self-contained sign-in / register card built on the design system.
 *
 * A single source of truth for the auth form: the segmented login/register
 * toggle, email + password (+ an optional display name on register), the
 * full-width primary action, and the register→login→me submit flow with toast
 * feedback. Reused by both the full-screen {@link AuthGate} and the header
 * account menu (as a centered modal), so the two never drift apart.
 */
export function AuthCard({ config, onLogin, onSuccess, className }: AuthCardProps) {
  const toast = useToast();
  const { t } = useT();
  const [mode, setMode] = useState<Mode>("login");
  const [emailInput, setEmailInput] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);

  const canSubmit = emailInput.trim().length > 0 && password.length > 0 && !loading;

  async function submit() {
    if (!canSubmit) return;
    setLoading(true);
    try {
      const trimmedEmail = emailInput.trim();
      if (mode === "register") {
        await register(trimmedEmail, password, config, displayName);
        toast.push(t("auth.accountCreated"), "success");
      }
      const { access_token } = await login(trimmedEmail, password, config);
      // Confirm the token resolves and read back the canonical identity.
      const user: AuthUser = await me({ ...config, token: access_token });
      onLogin(access_token, user.email, user.display_name ?? null);
      toast.push(
        t("auth.signedInToast", { email: user.display_name || user.email }),
        "success",
      );
      onSuccess?.();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : t("auth.failed"), "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className={cn("w-full max-w-sm animate-fade-in", className)}>
      <CardBody className="p-6 sm:p-8">
        <div className="flex flex-col items-center text-center">
          <BrandMark className="h-12 w-12" />
          <h1 className="mt-4 text-lg font-semibold text-ink">{t("auth.cardTitle")}</h1>
          <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">
            {t("auth.cardSubtitle")}
          </p>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex rounded-lg border border-zinc-200 p-0.5 text-sm dark:border-zinc-700">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                aria-pressed={mode === m}
                className={cn(
                  "flex-1 rounded-md px-2 py-1.5 font-medium transition-colors",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500",
                  mode === m
                    ? "bg-brand-600 text-white dark:bg-brand-500"
                    : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-300 dark:hover:bg-zinc-800",
                )}
              >
                {m === "login" ? t("auth.signIn") : t("auth.register")}
              </button>
            ))}
          </div>

          <TextField
            label={t("auth.email")}
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
          />

          {mode === "register" && (
            <TextField
              label={t("auth.displayName")}
              type="text"
              autoComplete="nickname"
              placeholder={t("auth.displayNamePlaceholder")}
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          )}

          <TextField
            label={t("auth.password")}
            type="password"
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            placeholder="••••••••"
            hint={mode === "register" ? t("auth.passwordHint") : undefined}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />

          <Button className="w-full" onClick={submit} loading={loading} disabled={!canSubmit}>
            {mode === "login" ? t("auth.signIn") : t("auth.createAccount")}
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
