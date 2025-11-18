"use client";

import type React from "react";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import type { StatusPillVariant } from "@/components/common/StatusPill";

export type GlobalMessageType = StatusPillVariant;

export interface GlobalMessage {
  /**Unique identifier for the message. */
  id: number;
  /**Message text to display. */
  text: string;
  /**Message visual/semantic variant. */
  type: GlobalMessageType;
}

export interface ShowMessageOptions {
  /**Duration in milliseconds before the message auto-dismisses. */
  durationMs?: number;
}

interface GlobalMessageContextValue {
  /**Current list of global messages. */
  messages: GlobalMessage[];
  /**
   * Publish a global message with the given type.
   *
   * Parameters
   * ----------
   * type : GlobalMessageType
   *     Visual/semantic variant of the message.
   * text : string
   *     Message text to display.
   * options : ShowMessageOptions, optional
   *     Additional configuration such as duration.
   */
  showMessage: (
    type: GlobalMessageType,
    text: string,
    options?: ShowMessageOptions,
  ) => void;
  /**Convenience helper for success messages. */
  showSuccess: (text: string, options?: ShowMessageOptions) => void;
  /**Convenience helper for info messages. */
  showInfo: (text: string, options?: ShowMessageOptions) => void;
  /**Convenience helper for warning messages. */
  showWarning: (text: string, options?: ShowMessageOptions) => void;
  /**Convenience helper for danger/error messages. */
  showDanger: (text: string, options?: ShowMessageOptions) => void;
  /**Convenience helper for neutral messages. */
  showNeutral: (text: string, options?: ShowMessageOptions) => void;
  /**Remove a message immediately. */
  removeMessage: (id: number) => void;
  /**Clear all messages. */
  clearMessages: () => void;
}

const GlobalMessageContext = createContext<
  GlobalMessageContextValue | undefined
>(undefined);

const DEFAULT_DURATION_MS = 3000;

/**
 * Provider for global message publishing and subscription.
 *
 * Wraps part of the React tree and exposes a simple API to publish
 * messages from anywhere, while a dedicated display component can
 * subscribe and render them.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     React node tree to wrap with the provider.
 */
export function GlobalMessageProvider({
  children,
}: {
  children: ReactNode;
}): React.ReactElement {
  const [messages, setMessages] = useState<GlobalMessage[]>([]);
  const nextIdRef = useRef(1);
  const timeoutIdsRef = useRef<Map<number, number>>(new Map());

  const removeMessage = useCallback((id: number) => {
    setMessages((prev) => prev.filter((message) => message.id !== id));
    const timeoutId = timeoutIdsRef.current.get(id);
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId);
      timeoutIdsRef.current.delete(id);
    }
  }, []);

  const showMessage = useCallback(
    (type: GlobalMessageType, text: string, options?: ShowMessageOptions) => {
      const id = nextIdRef.current++;
      const durationMs = options?.durationMs ?? DEFAULT_DURATION_MS;

      setMessages((prev) => [...prev, { id, text, type }]);

      if (durationMs > 0 && typeof window !== "undefined") {
        const timeoutId = window.setTimeout(() => {
          removeMessage(id);
        }, durationMs);
        timeoutIdsRef.current.set(id, timeoutId);
      }
    },
    [removeMessage],
  );

  const clearMessages = useCallback(() => {
    setMessages((prev) => {
      prev.forEach((message) => {
        const timeoutId = timeoutIdsRef.current.get(message.id);
        if (timeoutId !== undefined) {
          clearTimeout(timeoutId);
          timeoutIdsRef.current.delete(message.id);
        }
      });
      return [];
    });
  }, []);

  const value: GlobalMessageContextValue = useMemo(
    () => ({
      messages,
      showMessage,
      showSuccess: (text, options) =>
        showMessage("success", text, options ?? {}),
      showInfo: (text, options) => showMessage("info", text, options ?? {}),
      showWarning: (text, options) =>
        showMessage("warning", text, options ?? {}),
      showDanger: (text, options) => showMessage("danger", text, options ?? {}),
      showNeutral: (text, options) =>
        showMessage("neutral", text, options ?? {}),
      removeMessage,
      clearMessages,
    }),
    [messages, showMessage, removeMessage, clearMessages],
  );

  return (
    <GlobalMessageContext.Provider value={value}>
      {children}
    </GlobalMessageContext.Provider>
  );
}

/**
 * Hook to access the global message context.
 *
 * Returns
 * -------
 * GlobalMessageContextValue
 *     The current global message state and publishing helpers.
 *
 * Raises
 * ------
 * Error
 *     If used outside of a GlobalMessageProvider.
 */
export function useGlobalMessages(): GlobalMessageContextValue {
  const context = useContext(GlobalMessageContext);
  if (context === undefined) {
    throw new Error(
      "useGlobalMessages must be used within a GlobalMessageProvider",
    );
  }
  return context;
}
