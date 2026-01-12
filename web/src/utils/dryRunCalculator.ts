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

import type { BookMergeRecommendation } from "@/services/bookService";

type BookDetail = BookMergeRecommendation["books"][0];

export interface DryRunStep {
  type:
    | "keep"
    | "metadata"
    | "cover"
    | "file_conflict"
    | "file_move"
    | "delete"
    | "result";
  description: string;
  icon: string;
  textColor: string;
}

const STEP_CONFIGS: Record<
  DryRunStep["type"],
  Pick<DryRunStep, "icon" | "textColor">
> = {
  keep: { icon: "pi-check-circle", textColor: "text-green-500" },
  metadata: { icon: "pi-arrow-right", textColor: "text-primary-a0" },
  cover: { icon: "pi-image", textColor: "text-primary-a0" },
  file_conflict: {
    icon: "pi-exclamation-circle",
    textColor: "text-orange-500",
  },
  file_move: { icon: "pi-arrow-right", textColor: "text-primary-a0" },
  delete: { icon: "pi-trash", textColor: "text-orange-500" },
  result: { icon: "pi-check", textColor: "text-primary-a0 font-semibold" },
};

function createDryRunStep(
  type: DryRunStep["type"],
  description: string,
): DryRunStep {
  const config = STEP_CONFIGS[type];
  return { type, description, ...config };
}

export class DryRunCalculator {
  constructor(
    private books: BookDetail[],
    private keepId: number,
  ) {}

  calculate(): DryRunStep[] {
    const keepBook = this.books.find((b) => b.id === this.keepId);
    const mergeBooks = this.books.filter((b) => b.id !== this.keepId);

    if (!keepBook) return [];

    const steps: DryRunStep[] = [];

    steps.push(this.createKeepStep(keepBook));

    mergeBooks.forEach((mergeBook) => {
      steps.push(...this.createMergeSteps(keepBook, mergeBook));
      steps.push(this.createDeleteStep(mergeBook));
    });

    steps.push(this.createResultStep(keepBook));

    return steps;
  }

  private createKeepStep(keepBook: BookDetail): DryRunStep {
    return createDryRunStep(
      "keep",
      `Keep "${keepBook.title}" (ID: ${keepBook.id})`,
    );
  }

  private createMergeSteps(
    keepBook: BookDetail,
    mergeBook: BookDetail,
  ): DryRunStep[] {
    const steps: DryRunStep[] = [];

    // Metadata
    steps.push(
      createDryRunStep(
        "metadata",
        `Merge metadata from "${mergeBook.title}" into "${keepBook.title}" (filling empty fields)`,
      ),
    );

    // Cover
    if (mergeBook.has_cover) {
      const coverDescription = !keepBook.has_cover
        ? `Copy cover from "${mergeBook.title}" to "${keepBook.title}"`
        : `Compare covers: if "${mergeBook.title}" has better quality, replace "${keepBook.title}" cover`;

      steps.push(createDryRunStep("cover", coverDescription));
    }

    // Files
    if (mergeBook.formats?.length > 0) {
      steps.push(...this.createFileSteps(keepBook, mergeBook));
    }

    return steps;
  }

  private createFileSteps(
    keepBook: BookDetail,
    mergeBook: BookDetail,
  ): DryRunStep[] {
    return mergeBook.formats.map((fmt) => {
      const keepFormat = keepBook.formats?.find((f) => f.format === fmt.format);

      if (keepFormat) {
        return createDryRunStep(
          "file_conflict",
          `File conflict for ${fmt.format}: If merged file is larger, replace keep file (backing up original as .bak). Otherwise backup merged file as .bak.`,
        );
      }

      return createDryRunStep(
        "file_move",
        `Move ${fmt.format} file from "${mergeBook.title}" to "${keepBook.title}"`,
      );
    });
  }

  private createDeleteStep(mergeBook: BookDetail): DryRunStep {
    return createDryRunStep(
      "delete",
      `Delete "${mergeBook.title}" (ID: ${mergeBook.id}) after merge`,
    );
  }

  private createResultStep(keepBook: BookDetail): DryRunStep {
    return createDryRunStep(
      "result",
      `Final result: "${keepBook.title}" will contain merged files and metadata`,
    );
  }
}
