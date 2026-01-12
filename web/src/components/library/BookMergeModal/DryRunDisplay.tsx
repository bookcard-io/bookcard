// Copyright (C) 2026 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import type React from "react";
import { cn } from "@/libs/utils";
import type { DryRunStep } from "@/utils/dryRunCalculator";

interface DryRunDisplayProps {
  steps: DryRunStep[];
  scrollRef: React.RefObject<HTMLDivElement | null>;
}

export function DryRunDisplay({ steps, scrollRef }: DryRunDisplayProps) {
  return (
    <div
      ref={scrollRef}
      className="mt-6 rounded-md border border-primary-a0/30 bg-primary-a0/5 p-4"
    >
      <h3 className="mb-3 font-semibold text-[var(--color-text-a0)] text-sm">
        Dry Run - Merge Steps
      </h3>
      <ol className="space-y-2 text-sm">
        {steps.map((step, index) => (
          <li
            key={`${step.type}-${index}`}
            className={cn("flex items-start gap-2", step.textColor)}
          >
            <i className={cn("pi mt-0.5", step.icon)} aria-hidden="true" />
            <span>{step.description}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
