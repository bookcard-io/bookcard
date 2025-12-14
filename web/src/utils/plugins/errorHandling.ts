import type { PluginListResult } from "@/services/pluginService";

export type PluginStatusType = NonNullable<PluginListResult["statusType"]>;

export interface PluginStatus {
  message: string;
  type: PluginStatusType;
}

type ErrorWithPluginType = Error & {
  errorType?: string;
  messageType?: string;
};

const STATUS_TYPES: ReadonlySet<PluginStatusType> = new Set([
  "warning",
  "error",
  "success",
  "info",
  "neutral",
]);

function isPluginStatusType(value: unknown): value is PluginStatusType {
  return (
    typeof value === "string" && STATUS_TYPES.has(value as PluginStatusType)
  );
}

/**
 * Extract a structured status (message + type) from a typed plugin-service error.
 *
 * The backend may return a structured error payload (e.g. calibre_not_found)
 * which `pluginService` turns into an `Error` with `errorType` and `messageType`.
 *
 * Parameters
 * ----------
 * error : unknown
 *     Error value thrown by a plugin operation.
 *
 * Returns
 * -------
 * PluginStatus | null
 *     Parsed status if available; otherwise null.
 */
export function getPluginStatusFromError(error: unknown): PluginStatus | null {
  if (!(error instanceof Error)) {
    return null;
  }

  const typed = error as ErrorWithPluginType;
  if (!typed.errorType) {
    return null;
  }

  const statusType: PluginStatusType = isPluginStatusType(typed.messageType)
    ? typed.messageType
    : "neutral";

  return {
    message: typed.message || "Unknown error",
    type: statusType,
  };
}
