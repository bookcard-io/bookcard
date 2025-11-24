// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { endSession, startSession } from "@/services/readingService";
import type { ReadingSession, ReadingSessionCreate } from "@/types/reading";

export interface UseReadingSessionOptions {
  /** Book ID. */
  bookId: number;
  /** Book format (EPUB, PDF, etc.). */
  format: string;
  /** Device identifier (optional). */
  device?: string | null;
  /** Whether to automatically start session on mount. */
  autoStart?: boolean;
  /** Whether to automatically end session on unmount. */
  autoEnd?: boolean;
  /** Callback when session starts. */
  onSessionStart?: (session: ReadingSession) => void;
  /** Callback when session ends. */
  onSessionEnd?: (session: ReadingSession) => void;
}

export interface UseReadingSessionResult {
  /** Current session ID. */
  sessionId: number | null;
  /** Whether session is active. */
  isActive: boolean;
  /** Whether session is starting. */
  isStarting: boolean;
  /** Whether session is ending. */
  isEnding: boolean;
  /** Error message if operation failed. */
  error: string | null;
  /** Function to start session. */
  start: () => Promise<ReadingSession | null>;
  /** Function to end session. */
  end: (progressEnd: number) => Promise<ReadingSession | null>;
}

/**
 * Custom hook for managing reading session lifecycle.
 *
 * Handles automatic session start/end and progress tracking.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseReadingSessionOptions
 *     Hook options including book ID and format.
 *
 * Returns
 * -------
 * UseReadingSessionResult
 *     Session state and control functions.
 */
export function useReadingSession(
  options: UseReadingSessionOptions,
): UseReadingSessionResult {
  const {
    bookId,
    format,
    device = null,
    autoStart = true,
    autoEnd = true,
    onSessionStart,
    onSessionEnd,
  } = options;

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const hasStartedRef = useRef(false);
  const isStartingRef = useRef(false);
  const autoStartAttemptedRef = useRef<string | null>(null);
  const isEndingRef = useRef(false);
  const endedSessionIdRef = useRef<number | null>(null);

  const startMutation = useMutation<
    ReadingSession,
    Error,
    ReadingSessionCreate
  >({
    mutationFn: startSession,
    onSuccess: (data) => {
      setSessionId(data.id);
      setError(null);
      hasStartedRef.current = true;
      endedSessionIdRef.current = null; // Reset ended ref when new session starts
      onSessionStart?.(data);
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["reading-sessions"] });
    },
    onError: (err) => {
      setError(err.message);
      hasStartedRef.current = false; // Allow retry on error
      autoStartAttemptedRef.current = null;
    },
  });

  const endMutation = useMutation<
    ReadingSession,
    Error,
    { sessionId: number; progressEnd: number }
  >({
    mutationFn: ({ sessionId, progressEnd }) =>
      endSession(sessionId, progressEnd),
    onSuccess: (data) => {
      setSessionId(null);
      setError(null);
      isEndingRef.current = false;
      onSessionEnd?.(data);
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["reading-sessions"] });
      queryClient.invalidateQueries({ queryKey: ["reading-history"] });
    },
    onError: (err) => {
      setError(err.message);
      isEndingRef.current = false;
      endedSessionIdRef.current = null; // Allow retry on error
    },
  });

  const start = useCallback(async () => {
    if (sessionId !== null || isStartingRef.current) {
      return null; // Session already started or starting
    }

    isStartingRef.current = true;
    setIsStarting(true);
    try {
      const session = await startMutation.mutateAsync({
        book_id: bookId,
        format,
        device,
      });
      hasStartedRef.current = true;
      return session;
    } catch (_err) {
      return null;
    } finally {
      isStartingRef.current = false;
      setIsStarting(false);
    }
  }, [bookId, format, device, sessionId, startMutation]);

  const end = useCallback(
    async (progressEnd: number) => {
      if (
        sessionId === null ||
        isEndingRef.current ||
        endedSessionIdRef.current === sessionId
      ) {
        return null; // No active session, already ending, or already ended
      }

      isEndingRef.current = true;
      endedSessionIdRef.current = sessionId;
      setIsEnding(true);
      try {
        const session = await endMutation.mutateAsync({
          sessionId,
          progressEnd,
        });
        return session;
      } catch (_err) {
        endedSessionIdRef.current = null; // Allow retry on error
        return null;
      } finally {
        isEndingRef.current = false;
        setIsEnding(false);
      }
    },
    [sessionId, endMutation],
  );

  // Auto-start session on mount (only once per bookId/format combination)
  useEffect(() => {
    const sessionKey = `${bookId}-${format}`;
    if (
      autoStart &&
      bookId > 0 &&
      format &&
      sessionId === null &&
      !hasStartedRef.current &&
      !isStartingRef.current &&
      autoStartAttemptedRef.current !== sessionKey
    ) {
      autoStartAttemptedRef.current = sessionKey;
      isStartingRef.current = true;
      setIsStarting(true);
      startMutation
        .mutateAsync({
          book_id: bookId,
          format,
          device,
        })
        .then(() => {
          hasStartedRef.current = true;
        })
        .catch(() => {
          // Error already handled by mutation
          autoStartAttemptedRef.current = null; // Allow retry on error
        })
        .finally(() => {
          isStartingRef.current = false;
          setIsStarting(false);
        });
    }
    // Reset refs when bookId or format changes
    if (
      autoStartAttemptedRef.current &&
      autoStartAttemptedRef.current !== sessionKey
    ) {
      hasStartedRef.current = false;
      autoStartAttemptedRef.current = null;
    }
  }, [autoStart, bookId, format, device, sessionId, startMutation]);

  // Auto-end session on unmount or page visibility change
  useEffect(() => {
    if (!autoEnd || sessionId === null) {
      return;
    }

    const currentSessionId = sessionId; // Capture current session ID

    const handleVisibilityChange = () => {
      if (
        document.hidden &&
        currentSessionId !== null &&
        !isEndingRef.current &&
        endedSessionIdRef.current !== currentSessionId
      ) {
        // Get current progress from query cache if available
        const progressData = queryClient.getQueryData<{ progress: number }>([
          "reading-progress",
          bookId,
          format,
        ]);
        const currentProgress = progressData?.progress ?? 0;
        void end(currentProgress);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      // End session on unmount
      if (
        currentSessionId !== null &&
        !isEndingRef.current &&
        endedSessionIdRef.current !== currentSessionId
      ) {
        const progressData = queryClient.getQueryData<{ progress: number }>([
          "reading-progress",
          bookId,
          format,
        ]);
        const currentProgress = progressData?.progress ?? 0;
        void end(currentProgress);
      }
    };
  }, [autoEnd, sessionId, bookId, format, end, queryClient]);

  return {
    sessionId,
    isActive: sessionId !== null,
    isStarting: isStarting || startMutation.isPending,
    isEnding: isEnding || endMutation.isPending,
    error:
      error ||
      startMutation.error?.message ||
      endMutation.error?.message ||
      null,
    start,
    end,
  };
}
