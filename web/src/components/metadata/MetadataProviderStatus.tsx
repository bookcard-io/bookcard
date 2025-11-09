"use client";

import type { ProviderStatus } from "@/hooks/useMetadataSearchStream";
import styles from "./MetadataProviderStatus.module.scss";

export interface MetadataProviderStatusProps {
  /** Provider status information. */
  status: ProviderStatus;
}

/**
 * Component for displaying individual provider search status.
 *
 * Follows SRP by focusing solely on provider status visualization.
 */
export function MetadataProviderStatus({
  status,
}: MetadataProviderStatusProps) {
  const getStatusIcon = () => {
    switch (status.status) {
      case "pending":
        return <div className={styles.iconPending}>○</div>;
      case "searching":
        return <div className={styles.iconSearching}>⟳</div>;
      case "completed":
        return <div className={styles.iconCompleted}>✓</div>;
      case "failed":
        return <div className={styles.iconFailed}>✗</div>;
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
    <div className={styles.container} data-status={status.status}>
      <div className={styles.header}>
        <div className={styles.iconContainer}>{getStatusIcon()}</div>
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
