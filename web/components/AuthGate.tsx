"use client";

import { useState } from "react";
import { login, me, register, type AuthUser, type ConnectionConfig } from "@/lib/api";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { useToast } from "@/components/Toast";
import { useT } from "@/lib/i18n";
import { BrandMark } from "@/components/Logo";
import { LanguageToggle } from "@/components/LanguageToggle";
import { cn } from "@/lib/cn";

interface AuthGateProps {
  config: ConnectionConfig;
  onLogin: (token: string, email: string) => void;
}

type Mode = "login" | "register";

/**
 * Full-screen blocking sign-in gate shown when the backend enforces
 * authentication (`require_auth`) and the visitor has no token yet. It reuses
 * the same register/login/me flow as the header account menu, but as a centered
 * card that stands in for the whole app until the user is signed in.
 */
export function AuthGate({ config, onLogin }: AuthGateProps) {
  const toast = useToast();
  const { t } = useT();
  const [mode, setMode] = useState<Mode>("login");
  const [emailInput, setEmailInput] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const canSubmit = emailInput.trim().length > 0 && password.length > 0 && !loading;

  async function submit() {
    if (!canSubmit) return;
    setLoading(true);
    try {
      const trimmedEmail = emailInput.trim();
      if (mode === "register") {
        await register(trimmedEmail, password, config);
        toast.push(t("auth.accountCreated"), "success");
      }
      const { access_token } = await login(trimmedEmail, password, config);
      // Confirm the token resolves and read back the canonical email.
      const user: AuthUser = await me({ ...config, token: access_token });
      onLogin(access_token, user.email);
      toast.push(t("auth.signedInToast", { email: user.email }), "success");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : t("auth.failed"), "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <header className="flex items-center justify-between px-4 py-4 sm:px-6 sm:py-5">
        <div className="flex items-center gap-3">
          <BrandMark className="h-10 w-10" />
          <div className="leading-tight">
            <p className="text-sm font-semibold text-ink">{t("app.name")}</p>
            <p className="text-xs text-zinc-500">{t("app.tagline")}</p>
          </div>
        </div>
        <LanguageToggle />
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-6 shadow-card dark:border-zinc-700 dark:bg-zinc-900 sm:p-8">
          <div className="mb-6 text-center">
            <h1 className="text-lg font-semibold text-ink">{t("gate.title")}</h1>
            <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">{t("gate.subtitle")}</p>
          </div>

          <div className="space-y-3">
            <div className="flex rounded-lg border border-zinc-200 p-0.5 text-sm dark:border-zinc-700">
              {(["login", "register"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={cn(
                    "flex-1 rounded-md px-2 py-1 font-medium transition-colors",
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
        </div>
      </main>
    </div>
  );
}
