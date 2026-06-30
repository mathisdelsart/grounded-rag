"use client";

import { useT } from "@/lib/i18n";
import { scrollToId } from "@/lib/scroll";

/** Closing call-to-action that scrolls down into the tool. */
export function LandingCta({ targetId = "tool" }: { targetId?: string }) {
  const { t } = useT();
  return (
    <section
      aria-labelledby="landing-cta-heading"
      className="relative overflow-hidden rounded-[2rem] border border-navy-900 bg-navy px-6 py-20 text-center shadow-xl sm:px-10 sm:py-28"
    >
      {/* Layered radial glows — a "trust / quality" highlight. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(70%_70%_at_50%_0%,theme(colors.brand.500/28%),transparent_70%)]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-24 left-1/2 h-64 w-[36rem] -translate-x-1/2 rounded-full bg-brand-500/10 blur-3xl"
      />
      <div className="relative mx-auto max-w-2xl">
        <h2
          id="landing-cta-heading"
          className="text-balance text-3xl font-bold tracking-tight text-white sm:text-5xl"
        >
          {t("landing.cta.title")}
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-pretty text-base leading-relaxed text-zinc-300 sm:text-lg">
          {t("landing.cta.body")}
        </p>
        <div className="mt-10 flex justify-center">
          <button
            type="button"
            onClick={() => scrollToId(targetId)}
            aria-label={t("hero.ctaAria")}
            className="group inline-flex items-center justify-center gap-2.5 rounded-2xl bg-brand-500 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-brand-900/40 transition hover:-translate-y-0.5 hover:bg-brand-400 hover:shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2 focus-visible:ring-offset-navy"
          >
            {t("landing.cta.button")}
            <svg
              aria-hidden
              viewBox="0 0 24 24"
              className="h-5 w-5 transition-transform group-hover:translate-x-0.5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </button>
        </div>
      </div>
    </section>
  );
}
