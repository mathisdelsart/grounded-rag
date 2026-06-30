"use client";

import { Fragment } from "react";
import { useT, type Locale } from "@/lib/i18n";
import { cn } from "@/lib/cn";

const OPTIONS: Locale[] = ["fr", "en", "nl"];

/**
 * Discreet header language switcher: plain uppercase text codes (FR · EN · NL)
 * with the active one emphasised — no boxed segmented control. The active locale
 * is resolved and persisted by the i18n provider.
 */
export function LanguageToggle() {
  const { locale, setLocale, t } = useT();
  return (
    <div
      role="radiogroup"
      aria-label={t("lang.label")}
      className="flex items-center text-xs font-medium"
    >
      {OPTIONS.map((code, i) => {
        const active = locale === code;
        return (
          <Fragment key={code}>
            {i > 0 && <span className="px-1 text-zinc-300">/</span>}
            <button
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => setLocale(code)}
              className={cn(
                "rounded uppercase tracking-wide transition-colors",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2",
                active ? "text-ink" : "text-zinc-400 hover:text-zinc-700",
              )}
            >
              {code}
            </button>
          </Fragment>
        );
      })}
    </div>
  );
}
