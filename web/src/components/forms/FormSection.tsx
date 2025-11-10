"use client";

import type { ReactNode } from "react";
import { cn } from "@/libs/utils";

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
    <section
      className={cn(
        "flex flex-col gap-6 pb-6 border-b border-surface-a20",
        "last:border-b-0 last:pb-0",
        className,
      )}
    >
      <div className="mb-0">
        <h2 className="text-lg font-semibold text-text-a0 mb-2 leading-[1.4] m-0">
          {title}
        </h2>
        {description && (
          <p className="text-sm text-text-a30 m-0 leading-normal">{description}</p>
        )}
      </div>
      <div className="flex flex-col gap-5 md:grid md:grid-cols-3">{children}</div>
    </section>
  );
}
