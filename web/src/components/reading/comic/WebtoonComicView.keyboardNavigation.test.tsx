// Copyright (C) 2025 knguyen and others
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

import { render, waitFor } from "@testing-library/react";
import type React from "react";
import { act, forwardRef, useEffect, useImperativeHandle } from "react";
import { describe, expect, it, vi } from "vitest";

describe("WebtoonComicView keyboard navigation", () => {
  it("ArrowDown advances and ArrowUp decrements the page", async () => {
    vi.resetModules();

    const jumpToPage = vi.fn();
    const jumpToProgress = vi.fn();
    const scrollToPage = vi.fn();

    vi.doMock("./BaseVirtualizedComicView", () => {
      return {
        WEBTOON_CONFIG: {
          estimatedPageHeight: 800,
          overscan: 5,
          enableSnap: false,
        },
        BaseVirtualizedComicView: forwardRef(function MockBase(
          props: {
            totalPages: number;
            onPageChange: (
              page: number,
              totalPages: number,
              progress: number,
            ) => void;
          },
          ref: React.ForwardedRef<{
            jumpToPage: (page: number) => void;
            jumpToProgress: (progress: number) => void;
            scrollToPage: (page: number, behavior?: ScrollBehavior) => void;
          }>,
        ) {
          useImperativeHandle(ref, () => ({
            jumpToPage,
            jumpToProgress,
            scrollToPage,
          }));

          // Pretend page 3 is visible, so we can assert +/- 1 behavior.
          useEffect(() => {
            props.onPageChange(3, props.totalPages, 0.3);
          }, [props.onPageChange, props.totalPages]);

          return <div data-testid="mock-base" />;
        }),
      };
    });

    const { WebtoonComicView } = await import("./WebtoonComicView");

    const onPageChange = vi.fn();
    render(
      <WebtoonComicView
        bookId={1}
        format="cbz"
        totalPages={10}
        onPageChange={onPageChange}
      />,
    );

    // Ensure effects have run and the wrapper has seen a current page.
    await waitFor(() => expect(onPageChange).toHaveBeenCalled());

    await act(async () => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    });
    expect(scrollToPage).toHaveBeenCalledWith(4, "smooth");

    await act(async () => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
    });
    expect(scrollToPage).toHaveBeenCalledWith(2, "smooth");
    expect(jumpToPage).not.toHaveBeenCalled();
  });
});
