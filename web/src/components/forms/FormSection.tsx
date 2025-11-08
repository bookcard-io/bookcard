"use client";

import type { ReactNode } from "react";
import styles from "./FormSection.module.scss";

export interface FormSectionProps {
  /** Section title. */
  title: string;
  /** Section description/helper text. */
  description?: string;
  /** Section content. */
  children: ReactNode;
  /** Optional CSS class name. */
  className?: string;
}

/**
 * Form section component for grouping related form fields.
 *
 * Follows SRP by focusing solely on section layout and styling.
 * Uses composition pattern (IOC via children prop).
 */
export function FormSection({
  title,
  description,
  children,
  className,
}: FormSectionProps) {
  return (
    <section className={`${styles.section} ${className || ""}`}>
      <div className={styles.header}>
        <h2 className={styles.title}>{title}</h2>
        {description && <p className={styles.description}>{description}</p>}
      </div>
      <div className={styles.content}>{children}</div>
    </section>
  );
}
