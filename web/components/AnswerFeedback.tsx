"use client";

import { useState } from "react";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { useToast } from "@/components/Toast";
import { useT } from "@/lib/i18n";
import { sendFeedback, type ConnectionConfig, type FeedbackRating } from "@/lib/api";

/** Inline thumbs-up icon. */
function ThumbUpIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M7 10v11" />
      <path d="M7 10 11 3a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.4l-1.4 7A2 2 0 0 1 17.1 21H7" />
    </svg>
  );
}

/** Inline thumbs-down icon. */
function ThumbDownIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M17 14V3" />
      <path d="M17 14 13 21a2 2 0 0 1-2-2v-4H5.5a2 2 0 0 1-2-2.4l1.4-7A2 2 0 0 1 6.9 3H17" />
    </svg>
  );
}

interface AnswerFeedbackProps {
  studentId: string;
  question: string;
  answer: string;
  config: ConnectionConfig;
}

/**
 * Thumbs up/down on a tutor answer, posted to the backend for later evaluation.
 * A thumbs down reveals an optional note input before sending. Once submitted,
 * the controls are replaced by a brief confirmation.
 */
export function AnswerFeedback({ studentId, question, answer, config }: AnswerFeedbackProps) {
  const toast = useToast();
  const { t } = useT();
  const [showNote, setShowNote] = useState(false);
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(rating: FeedbackRating) {
    setSubmitting(true);
    try {
      await sendFeedback(
        { student_id: studentId, rating, question, answer, note: note || null },
        config,
      );
      setDone(true);
      toast.push(t("feedback.thanks"), "success");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : t("feedback.failed"), "error");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <p className="text-sm text-emerald-700 dark:text-emerald-300" role="status">
        {t("feedback.thanks")}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{t("feedback.prompt")}</p>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="ghost"
          onClick={() => submit(1)}
          loading={submitting}
          aria-label={t("feedback.upAria")}
        >
          <ThumbUpIcon />
          {t("feedback.up")}
        </Button>
        <Button
          variant="ghost"
          onClick={() => setShowNote(true)}
          disabled={submitting}
          aria-label={t("feedback.downAria")}
          aria-expanded={showNote}
        >
          <ThumbDownIcon />
          {t("feedback.down")}
        </Button>
      </div>
      {showNote && (
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-0 flex-1">
            <TextField
              aria-label={t("feedback.notePlaceholder")}
              placeholder={t("feedback.notePlaceholder")}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
          <Button variant="secondary" onClick={() => submit(-1)} loading={submitting}>
            {t("feedback.send")}
          </Button>
        </div>
      )}
    </div>
  );
}
