"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Animates the numeric part of `value` from zero up to its target the first time
 * it scrolls into view (e.g. "82 %" counts 0→82, keeping the prefix/suffix). A
 * one-shot IntersectionObserver triggers it; reduced-motion users and browsers
 * without the observer see the final value immediately.
 */
export function CountUp({ value, durationMs = 1400 }: { value: string; durationMs?: number }) {
  const match = value.match(/^(\D*)(\d[\d.,]*)(.*)$/);
  const prefix = match?.[1] ?? "";
  const target = match ? Number(match[2].replace(/[.,]/g, "")) : 0;
  const suffix = match?.[3] ?? "";

  const ref = useRef<HTMLSpanElement | null>(null);
  const [n, setN] = useState(match ? 0 : target);

  useEffect(() => {
    if (!match) return;
    const node = ref.current;
    if (!node) return;

    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduced || typeof IntersectionObserver === "undefined") {
      setN(target);
      return;
    }

    let raf = 0;
    let start = 0;
    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min(1, (ts - start) / durationMs);
      // Ease-out cubic for a snappy settle.
      const eased = 1 - Math.pow(1 - progress, 3);
      setN(Math.round(eased * target));
      if (progress < 1) raf = requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          raf = requestAnimationFrame(step);
          observer.disconnect();
        }
      },
      { threshold: 0.4 },
    );
    observer.observe(node);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(raf);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <span ref={ref}>
      {prefix}
      {n}
      {suffix}
    </span>
  );
}
