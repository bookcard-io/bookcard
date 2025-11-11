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
        "flex flex-col gap-6 border-surface-a20 border-b pb-6",
        "last:border-b-0 last:pb-0",
        className,
      )}
    >
      <div className="mb-0">
        <h2 className="m-0 mb-2 font-semibold text-lg text-text-a0 leading-[1.4]">
          {title}
        </h2>
        {description && (
          <p className="m-0 text-sm text-text-a30 leading-normal">
            {description}
          </p>
        )}
      </div>
      <div className="flex flex-col gap-5 md:grid md:grid-cols-3">
        {children}
      </div>
    </section>
  );
}
