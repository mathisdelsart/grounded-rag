"use client";

import { useEffect, useRef, useState } from "react";
import { getCourses, type ConnectionConfig } from "@/lib/api";

/** Result of {@link useCourses}: the owner-scoped course list and its status. */
export interface CoursesState {
  /** The user's indexed courses (owner-scoped). Empty while loading or on error. */
  courses: string[];
  /** True while the initial or a refreshed fetch is in flight. */
  loading: boolean;
  /** True when the last fetch failed (e.g. the backend is unreachable). */
  error: boolean;
}

/**
 * Single source of truth for the signed-in user's indexed courses, backed by
 * the owner-scoped `GET /courses`. Fetches on mount and whenever the connection
 * target, owner (`studentId`), or `refreshKey` changes — the latter is bumped
 * after a document upload so a freshly indexed course appears without a manual
 * refresh. Lifting this into one hook lets the page decide whether the user has
 * any material at all while feeding the same list to every course selector, so
 * the list is fetched once instead of once per panel.
 */
export function useCourses(
  config: ConnectionConfig,
  studentId?: string,
  refreshKey?: number,
): CoursesState {
  const [courses, setCourses] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Read the latest config without making it a dependency: the primitive
  // fields below are the real fetch inputs, so the effect re-runs on those.
  const configRef = useRef(config);
  configRef.current = config;

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(false);
    getCourses(configRef.current, studentId)
      .then((list) => {
        if (!active) return;
        setCourses(list);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setCourses([]);
        setError(true);
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [config.baseUrl, config.apiKey, config.token, studentId, refreshKey]);

  return { courses, loading, error };
}
