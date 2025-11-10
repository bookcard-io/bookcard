"use client";

import { useCallback } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import styles from "./MetadataResultItem.module.scss";

export interface MetadataResultItemProps {
  record: MetadataRecord;
  /** Callback when this item is selected. */
  onSelect?: (record: MetadataRecord) => void;
}

export function MetadataResultItem({
  record,
  onSelect,
}: MetadataResultItemProps) {
  const handleClick = useCallback(() => {
    onSelect?.(record);
  }, [onSelect, record]);

  return (
    <div className={styles.container}>
      <div className={styles.coverWrap}>
        {record.cover_url ? (
          <button
            type="button"
            onClick={handleClick}
            className={styles.coverButton}
            aria-label={`Load metadata for ${record.title}`}
            title="Click to load metadata to form"
          >
            <ImageWithLoading
              src={record.cover_url}
              alt={`Cover for ${record.title}`}
              width={60}
              height={90}
              className={styles.cover}
              unoptimized
            />
          </button>
        ) : (
          <div className={styles.coverPlaceholder} aria-hidden="true" />
        )}
      </div>
      <div className={styles.content}>
        <div className={styles.header}>
          <div className={styles.title}>{record.title}</div>
          {record.publisher && (
            <div className={styles.publisher}>{record.publisher}</div>
          )}
        </div>
        {record.authors && record.authors.length > 0 && (
          <div className={styles.metaRow}>
            <span className={styles.metaLabel}>Author</span>
            <span className={styles.metaValue}>
              {record.authors.join(", ")}
            </span>
          </div>
        )}
        {record.description && (
          <div className={styles.description} title={record.description}>
            {record.description}
          </div>
        )}
        <div className={styles.footer}>
          <a
            href={record.url}
            className={styles.sourceLink}
            target="_blank"
            rel="noreferrer"
          >
            Source: {record.source_id}
          </a>
        </div>
      </div>
    </div>
  );
}
