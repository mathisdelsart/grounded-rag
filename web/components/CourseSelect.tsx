"use client";

import { useEffect, useId } from "react";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/cn";

const baseField =
  "w-full rounded-lg border border-zinc-300 bg-white px-3.5 py-2.5 text-sm text-zinc-900 placeholder:text-zinc-400 " +
  "transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 " +
  "disabled:cursor-not-allowed disabled:bg-zinc-50 disabled:text-zinc-400 " +
  "dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500 " +
  "dark:focus:border-brand-400 dark:focus:ring-brand-400/20 dark:disabled:bg-zinc-800/50 dark:disabled:text-zinc-500";

interface CourseSelectProps {
  /** Current course filter value. Empty string means "All courses" (no filter). */
  value: string;
  /** Called with the chosen course, or an empty string for "All courses". */
  onChange: (course: string) => void;
  /** Owner-scoped course list, fetched once by the page and shared across panels. */
  courses: string[];
  /** True while the shared course list is still loading. */
  loading: boolean;
  /** True when the shared course list failed to load. */
  error: boolean;
  label?: string;
  hint?: string;
}

/**
 * Course filter backed by the page's owner-scoped course list. Renders an
 * accessible dropdown with an "All courses" option (sends no filter). If the
 * list is empty or failed to load, it degrades to a free-text input so the
 * filter never blocks the UI.
 *
 * A persisted selection is never trusted blindly: the stored course key lives
 * in localStorage and survives across accounts, so once the list has loaded a
 * value that is not in it (a stale choice, or one belonging to another account)
 * is reset to "" ("All courses"). The parent's `onChange` clears the stored key.
 */
export function CourseSelect({
  value,
  onChange,
  courses,
  loading,
  error,
  label,
  hint,
}: CourseSelectProps) {
  const { t } = useT();
  const id = useId();

  // Once the owner-scoped list has loaded, drop any selection that is not in it
  // (a course from a previous account/session, or one that no longer exists) so
  // the filter defaults to "All courses" rather than a phantom course.
  useEffect(() => {
    if (loading || error) return;
    if (value && !courses.includes(value)) onChange("");
  }, [loading, error, value, courses, onChange]);

  const resolvedLabel = label ?? t("ask.courseLabel");

  // Free-text fallback: request failed, or succeeded with no indexed courses.
  if (error || (!loading && courses.length === 0)) {
    const resolvedHint = error ? t("course.fetchFailed") : hint ?? t("ask.courseHint");
    return (
      <div className="space-y-1.5">
        <label
          htmlFor={id}
          className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          {resolvedLabel}
        </label>
        <input
          id={id}
          className={baseField}
          placeholder={t("ask.coursePlaceholder")}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <p className="text-xs text-zinc-500 dark:text-zinc-400">{resolvedHint}</p>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
      >
        {resolvedLabel}
      </label>
      <select
        id={id}
        className={cn(baseField, "pr-8")}
        value={value}
        disabled={loading}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">
          {loading ? t("course.loading") : t("course.allCourses")}
        </option>
        {courses.map((course) => (
          <option key={course} value={course}>
            {course}
          </option>
        ))}
      </select>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        {hint ?? t("ask.courseHint")}
      </p>
    </div>
  );
}
