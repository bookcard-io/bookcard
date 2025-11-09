"use client";

import type { SearchState } from "@/hooks/useMetadataSearchStream";
import styles from "./MetadataSearchProgress.module.scss";

export interface MetadataSearchProgressProps {
  /** Current search state. */
  state: SearchState;
}

/**
 * Component for displaying overall metadata search progress.
 *
 * Follows SRP by focusing solely on aggregate progress visualization.
 */
export function MetadataSearchProgress({ state }: MetadataSearchProgressProps) {
  const { totalProviders, providersCompleted, providersFailed, totalResults } =
    state;

  if (totalProviders === 0) {
    return null;
  }

  const providersInProgress =
    totalProviders - providersCompleted - providersFailed;
  const progressPercentage =
    totalProviders > 0
      ? ((providersCompleted + providersFailed) / totalProviders) * 100
      : 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>Search Progress</div>
        <div className={styles.stats}>
          {providersCompleted + providersFailed} / {totalProviders} providers
        </div>
      </div>

      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      <div className={styles.summary}>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Completed:</span>
          <span className={styles.summaryValue}>{providersCompleted}</span>
        </div>
        {providersInProgress > 0 && (
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>In Progress:</span>
            <span className={styles.summaryValue}>{providersInProgress}</span>
          </div>
        )}
        {providersFailed > 0 && (
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Failed:</span>
            <span
              className={`${styles.summaryValue} ${styles.summaryValueFailed}`}
            >
              {providersFailed}
            </span>
          </div>
        )}
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Total Results:</span>
          <span className={styles.summaryValue}>{totalResults}</span>
        </div>
      </div>
    </div>
  );
}
