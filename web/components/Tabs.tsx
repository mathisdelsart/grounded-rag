"use client";

import { useRef } from "react";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/cn";

export interface TabItem {
  id: string;
  label: string;
}

/**
 * Segmented tab strip. Controlled via `active` / `onChange`. Implements the
 * WAI-ARIA tabs pattern: roving tabindex with arrow-key navigation, and each
 * tab is linked to its panel through `id` / `aria-controls` (the panel carries
 * the matching `tabpanel-<id>` id and `aria-labelledby="tab-<id>"`). Horizontal
 * overflow is hinted with edge fades so hidden tabs stay discoverable on narrow
 * screens.
 */
export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: TabItem[];
  active: string;
  onChange: (id: string) => void;
}) {
  const { t } = useT();
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  function onKeyDown(e: React.KeyboardEvent, index: number) {
    let next = index;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") next = (index + 1) % tabs.length;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp")
      next = (index - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = tabs.length - 1;
    else return;
    e.preventDefault();
    const id = tabs[next].id;
    onChange(id);
    refs.current[id]?.focus();
  }

  return (
    <div className="relative">
      <div
        role="tablist"
        aria-label={t("tabs.aria")}
        className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {tabs.map((tab, index) => {
          const selected = tab.id === active;
          return (
            <button
              key={tab.id}
              ref={(el) => {
                refs.current[tab.id] = el;
              }}
              id={`tab-${tab.id}`}
              role="tab"
              type="button"
              aria-selected={selected}
              aria-controls={`tabpanel-${tab.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(tab.id)}
              onKeyDown={(e) => onKeyDown(e, index)}
              className={cn(
                "whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition-colors",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-zinc-950",
                selected
                  ? "bg-ink text-white shadow-sm dark:bg-white dark:text-ink"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800",
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      {/* Edge fades hint that the strip scrolls horizontally when it overflows. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-y-0 left-0 w-6 bg-gradient-to-r from-white to-transparent dark:from-zinc-950 sm:hidden"
      />
      <span
        aria-hidden
        className="pointer-events-none absolute inset-y-0 right-0 w-6 bg-gradient-to-l from-white to-transparent dark:from-zinc-950 sm:hidden"
      />
    </div>
  );
}
