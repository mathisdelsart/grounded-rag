import { cn } from "@/lib/cn";

/**
 * Brand mark: a graduation cap on a charcoal rounded square with a periwinkle
 * accent dot — signals "tutor / study" far better than a bare letter. Reused in
 * the header and footer, and mirrored by `app/icon.svg` (the favicon).
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-ink to-navy shadow-sm",
        className,
      )}
    >
      <svg
        viewBox="0 0 24 24"
        className="h-1/2 w-1/2"
        fill="none"
        stroke="white"
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M12 4 2 9l10 5 10-5-10-5Z" />
        <path d="M6 11.3V16c0 1.4 2.7 2.7 6 2.7s6-1.3 6-2.7v-4.7" />
        <path d="M22 9v3.5" />
      </svg>
      <span
        aria-hidden
        className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-brand-500 ring-2 ring-ink"
      />
    </span>
  );
}
