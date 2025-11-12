"use client";

import type { ProviderStatus } from "@/hooks/useMetadataSearchStream";
import styles from "./MetadataProviderStatus.module.scss";

export interface MetadataProviderStatusProps {
  /** Provider status information. */
  status: ProviderStatus;
  /** Whether the provider is enabled. */
  enabled: boolean;
  /** Callback when enable/disable toggle is clicked. */
  onToggle: () => void;
}

/**
 * Component for displaying individual provider search status.
 *
 * Follows SRP by focusing solely on provider status visualization.
 */
export function MetadataProviderStatus({
  status,
  enabled,
  onToggle,
}: MetadataProviderStatusProps) {
  const getStatusIcon = () => {
    switch (status.status) {
      case "pending":
        return (
          <i
            className={`pi pi-hourglass ${styles.iconPending}`}
            aria-hidden="true"
          />
        );
      case "searching":
        return (
          <i
            className={`pi pi-spin pi-spinner ${styles.iconSearching}`}
            aria-hidden="true"
          />
        );
      case "completed":
        return (
          <i
            className={`pi pi-check ${styles.iconCompleted}`}
            aria-hidden="true"
          />
        );
      case "failed":
        return (
          <i
            className={`pi pi-asterisk ${styles.iconFailed}`}
            aria-hidden="true"
          />
        );
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case "pending":
        return "Waiting...";
      case "searching":
        return status.discovered > 0
          ? `Found ${status.discovered}...`
          : "Searching...";
      case "completed":
        return `${status.resultCount} result${status.resultCount !== 1 ? "s" : ""}`;
      case "failed":
        return "Failed";
      default:
        return "";
    }
  };

  return (
    <div
      className={styles.container}
      data-status={status.status}
      data-enabled={enabled}
    >
      <div className={styles.header}>
        <div className={styles.iconContainer}>
          {getStatusIcon()}
          <button
            type="button"
            className={styles.enableIndicator}
            onClick={onToggle}
            aria-label={
              enabled ? `Disable ${status.name}` : `Enable ${status.name}`
            }
            aria-pressed={enabled}
            title={enabled ? "Disable provider" : "Enable provider"}
          >
            <i
              className={`pi ${enabled ? "pi-check-circle" : "pi-circle"} ${styles.enableIcon}`}
              aria-hidden="true"
            />
          </button>
        </div>
        <div className={styles.info}>
          <div className={styles.name}>{status.name}</div>
          <div className={styles.statusText}>{getStatusText()}</div>
        </div>
        {status.durationMs !== undefined && status.status === "completed" && (
          <div className={styles.duration}>
            {(status.durationMs / 1000).toFixed(1)}s
          </div>
        )}
      </div>
      {status.error && (
        <div className={styles.error} role="alert">
          <span className={styles.errorType}>
            {status.errorType || "Error"}:
          </span>{" "}
          {status.error}
        </div>
      )}
      {status.status === "searching" && status.discovered > 0 && (
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{
              width: `${Math.min((status.discovered / 20) * 100, 100)}%`,
            }}
          />
        </div>
      )}
    </div>
  );
}
