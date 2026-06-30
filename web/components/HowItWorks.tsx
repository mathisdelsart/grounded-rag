"use client";

import type { ReactNode } from "react";
import { useT } from "@/lib/i18n";
import type { TranslationKey } from "@/lib/i18n";
import { SectionIntro } from "@/components/SectionIntro";
import { Reveal } from "@/components/Reveal";

/** Stacked-layers icon — "index your course". */
function IndexIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="h-6 w-6"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 3 3 7.5 12 12l9-4.5L12 3Z" />
      <path d="m3 12 9 4.5L21 12" />
      <path d="m3 16.5 9 4.5 9-4.5" />
    </svg>
  );
}

/** Speech-bubble icon — "ask in natural language". */
function AskIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="h-6 w-6"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5A8.38 8.38 0 0 1 8 19l-5 1 1-4.5A8.38 8.38 0 0 1 3 11.5 8.5 8.5 0 0 1 11.5 3 8.5 8.5 0 0 1 21 11.5Z" />
    </svg>
  );
}

/** Document-with-check icon — "cited answer or refusal". */
function CitedIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="h-6 w-6"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" />
      <path d="M14 3v5h5" />
      <path d="m9 14 2 2 4-4" />
    </svg>
  );
}

interface Step {
  icon: ReactNode;
  title: TranslationKey;
  body: TranslationKey;
}

const STEPS: Step[] = [
  { icon: <IndexIcon />, title: "how.step1.title", body: "how.step1.body" },
  { icon: <AskIcon />, title: "how.step2.title", body: "how.step2.body" },
  { icon: <CitedIcon />, title: "how.step3.title", body: "how.step3.body" },
];

/**
 * Three concise steps as a horizontal stepper: numbered 01/02/03 nodes joined
 * by a thin connector line, each with a brand-tinted icon square that lifts and
 * tilts on hover. Steps reveal one after another as the section scrolls in.
 */
export function HowItWorks() {
  const { t } = useT();
  return (
    <section id="how" aria-labelledby="how-heading" className="scroll-mt-24 py-4">
      <Reveal>
        <SectionIntro
          eyebrow="how.eyebrow"
          title="how.title"
          subtitle="how.subtitle"
          headingId="how-heading"
        />
      </Reveal>

      <ol className="relative mt-16 grid gap-12 sm:grid-cols-3 sm:gap-8">
        {/* Connector line behind the nodes (desktop only). */}
        <div
          aria-hidden
          className="pointer-events-none absolute left-[16.67%] right-[16.67%] top-8 hidden h-px bg-gradient-to-r from-brand-200 via-brand-400 to-brand-200 sm:block"
        />
        {STEPS.map((step, i) => (
          <Reveal as="li" key={step.title} delay={i * 140} className="group relative text-center">
            <div className="flex justify-center">
              <span className="relative z-10 inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 to-white text-brand-600 shadow-sm transition duration-300 group-hover:-translate-y-1 group-hover:rotate-3 group-hover:shadow-lg group-hover:shadow-brand-500/20">
                {step.icon}
                <span className="absolute -right-2 -top-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-ink text-[11px] font-bold tabular-nums text-white shadow-sm">
                  {String(i + 1).padStart(2, "0")}
                </span>
              </span>
            </div>
            <h3 className="mt-6 text-lg font-semibold text-ink">{t(step.title)}</h3>
            <p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-zinc-600">
              {t(step.body)}
            </p>
          </Reveal>
        ))}
      </ol>
    </section>
  );
}
