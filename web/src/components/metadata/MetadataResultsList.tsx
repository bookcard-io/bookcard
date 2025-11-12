"use client";

import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { MetadataResultItem } from "./MetadataResultItem";
import styles from "./MetadataResultsList.module.scss";

export interface MetadataResultsListProps {
  results: MetadataRecord[];
  /** Callback when a metadata record is selected. */
  onSelectMetadata?: (record: MetadataRecord) => void;
}

export function MetadataResultsList({
  results,
  onSelectMetadata,
}: MetadataResultsListProps) {
  if (!results || results.length === 0) {
    return null;
  }

  // Track first occurrence of each source_id to add IDs for scrolling
  const seenSourceIds = new Set<string>();

  return (
    <div className={styles.container}>
      {results.map((r, idx) => {
        const isFirstForProvider = !seenSourceIds.has(r.source_id);
        if (isFirstForProvider) {
          seenSourceIds.add(r.source_id);
        }
        return (
          <MetadataResultItem
            key={`${r.source_id}:${r.external_id}:${idx}`}
            record={r}
            onSelect={onSelectMetadata}
            id={isFirstForProvider ? `result-${r.source_id}` : undefined}
          />
        );
      })}
    </div>
  );
}
