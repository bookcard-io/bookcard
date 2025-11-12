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

import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useModal } from "./useModal";

describe("useModal", () => {
  beforeEach(() => {
    document.body.style.overflow = "";
  });

  afterEach(() => {
    document.body.style.overflow = "";
  });

  it("should set body overflow to hidden when modal is open", () => {
    renderHook(() => useModal(true));
    expect(document.body.style.overflow).toBe("hidden");
  });

  it("should restore body overflow when modal is closed", () => {
    const { rerender } = renderHook(({ isOpen }) => useModal(isOpen), {
      initialProps: { isOpen: true },
    });
    expect(document.body.style.overflow).toBe("hidden");

    rerender({ isOpen: false });
    expect(document.body.style.overflow).toBe("auto");
  });

  it("should not change overflow when modal is closed", () => {
    renderHook(() => useModal(false));
    expect(document.body.style.overflow).toBe("");
  });

  it("should handle toggling modal state", () => {
    const { rerender } = renderHook(({ isOpen }) => useModal(isOpen), {
      initialProps: { isOpen: false },
    });

    rerender({ isOpen: true });
    expect(document.body.style.overflow).toBe("hidden");

    rerender({ isOpen: false });
    expect(document.body.style.overflow).toBe("auto");
  });
});
