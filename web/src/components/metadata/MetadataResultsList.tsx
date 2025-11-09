"use client";

import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { MetadataResultItem } from "./MetadataResultItem";
import styles from "./MetadataResultsList.module.scss";

export interface MetadataResultsListProps {
  results: MetadataRecord[];
}

export function MetadataResultsList({ results }: MetadataResultsListProps) {
  if (!results || results.length === 0) {
    return null;
  }
  return (
    <div className={styles.container}>
      {results.map((r, idx) => (
        <MetadataResultItem
          key={`${r.source_id}:${r.external_id}:${idx}`}
          record={r}
        />
      ))}
    </div>
  );
}
