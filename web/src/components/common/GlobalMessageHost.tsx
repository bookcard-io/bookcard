"use client";

import type { GlobalMessageType } from "@/contexts/GlobalMessageContext";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { cn } from "@/libs/utils";

/**
 * Host component for rendering global messages.
 *
 * Subscribes to the global message context and displays messages in
 * a floating container. This component is intentionally independent
 * so it can be positioned anywhere in the layout without coupling
 * to specific pages or headers.
 */

function getBackgroundColorForType(type: GlobalMessageType): string {
  switch (type) {
    case "success":
      return "var(--color-success-a0)";
    case "warning":
      return "var(--color-warning-a0)";
    case "danger":
      return "var(--color-danger-a0)";
    case "info":
      return "var(--color-info-a10)";
    case "neutral":
      return "var(--color-surface-a10)";
    default:
      return "var(--color-success-a0)";
  }
}

function getCloseButtonBackgroundColorForType(type: GlobalMessageType): string {
  switch (type) {
    case "success":
      return "var(--color-success-a10)";
    case "warning":
      return "var(--color-warning-a10)";
    case "danger":
      return "var(--color-danger-a10)";
    case "info":
      return "var(--color-info-a10)";
    case "neutral":
      return "var(--color-surface-a20)";
    default:
      return "var(--color-success-a10)";
  }
}

function getIconForType(type: GlobalMessageType): string {
  switch (type) {
    case "danger":
      return "pi-exclamation-circle";
    case "warning":
      return "pi-exclamation-triangle";
    case "info":
      return "pi-info-circle";
    case "success":
      return "pi-check-circle";
    case "neutral":
      return "pi-circle-off";
    default:
      return "pi-check-circle";
  }
}

export function GlobalMessageHost() {
  const { messages, removeMessage } = useGlobalMessages();

  if (messages.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        "fixed z-[60]",
        "right-4 bottom-4",
        "flex justify-end",
        "pointer-events-none",
      )}
    >
      <div className={cn("flex flex-col", "max-w-sm gap-2")}>
        {messages.map((message) => (
          <div
            key={message.id}
            className="pointer-events-auto flex items-center gap-3 rounded-md px-4 py-3 shadow-lg ring-1 ring-surface-a30 backdrop-blur-sm"
            style={{ backgroundColor: getBackgroundColorForType(message.type) }}
          >
            <div className="flex flex-1 items-center gap-3">
              <i
                className={cn("pi", getIconForType(message.type), "text-base")}
              />
              <div className="text-sm text-text-a0">{message.text}</div>
            </div>
            <button
              type="button"
              className={cn(
                "flex h-5 w-5 shrink-0 items-center justify-center",
                "rounded-full",
                "text-text-a0",
                "transition-colors duration-200",
                "hover:opacity-80",
                "active:opacity-60",
              )}
              style={{
                backgroundColor: getCloseButtonBackgroundColorForType(
                  message.type,
                ),
              }}
              onClick={() => {
                removeMessage(message.id);
              }}
              aria-label="Dismiss notification"
            >
              <i className="pi pi-times text-xs" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
