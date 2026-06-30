"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import {
  createSession,
  listSessions,
  type ConnectionConfig,
  type SessionOut,
} from "@/lib/api";
import { useT } from "@/lib/i18n";
import { useToast } from "@/components/Toast";
import { cn } from "@/lib/cn";

const baseField =
  "w-full rounded-lg border border-zinc-300 bg-white px-3.5 py-2.5 text-sm text-zinc-900 " +
  "transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 " +
  "disabled:cursor-not-allowed disabled:bg-zinc-50 disabled:text-zinc-400 " +
  "dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 " +
  "dark:focus:border-brand-400 dark:focus:ring-brand-400/20 dark:disabled:bg-zinc-800/50 dark:disabled:text-zinc-500";

interface ThreadSelectProps {
  studentId: string;
  config: ConnectionConfig;
  /** Active thread id, or null for "All history (no thread)". */
  value: number | null;
  /** Called with the chosen thread id, or null for "All history". */
  onChange: (id: number | null) => void;
}

/**
 * Compact thread switcher rendered in the tool frame so the active conversation
 * thread is visible and changeable from every tab. Threads are fetched via
 * `listSessions`; the list degrades gracefully to just "All history" on an empty
 * result or fetch error. A "+ New thread" affordance opens a fresh thread and
 * selects it. The selection itself lives in the page (`activeSessionId`), so this
 * control only reflects `value` and reports changes through `onChange`.
 */
export function ThreadSelect({
  studentId,
  config,
  value,
  onChange,
}: ThreadSelectProps) {
  const { t } = useT();
  const toast = useToast();
  const id = useId();
  const [sessions, setSessions] = useState<SessionOut[]>([]);
  const [creating, setCreating] = useState(false);

  const configRef = useRef(config);
  configRef.current = config;

  const load = useCallback(() => {
    let active = true;
    listSessions(studentId, configRef.current)
      .then((rows) => {
        if (active) setSessions(rows);
      })
      .catch(() => {
        if (active) setSessions([]);
      });
    return () => {
      active = false;
    };
    // Re-run when the student or connection target changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId, config.baseUrl, config.apiKey, config.token]);

  useEffect(() => load(), [load]);

  async function onCreate() {
    setCreating(true);
    try {
      const created = await createSession(studentId, null, configRef.current);
      setSessions((prev) => [created, ...prev]);
      onChange(created.id);
      toast.push(t("threadSelect.created"), "success");
    } catch (err) {
      toast.push(
        err instanceof Error ? err.message : t("threads.createFailed"),
        "error",
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
      >
        {t("threadSelect.label")}
      </label>
      <div className="flex items-center gap-2">
        <select
          id={id}
          className={cn(baseField, "pr-8")}
          value={value == null ? "" : String(value)}
          onChange={(e) =>
            onChange(e.target.value === "" ? null : Number(e.target.value))
          }
        >
          <option value="">{t("threadSelect.all")}</option>
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title?.trim() || t("threads.untitled")}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={onCreate}
          disabled={creating}
          className="shrink-0 whitespace-nowrap rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 dark:focus-visible:ring-offset-zinc-950"
        >
          {t("threadSelect.new")}
        </button>
      </div>
    </div>
  );
}
