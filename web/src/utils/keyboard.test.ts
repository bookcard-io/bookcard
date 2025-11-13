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

import { describe, expect, it, vi } from "vitest";
import { createEnterSpaceHandler } from "./keyboard";

describe("keyboard utils", () => {
  describe("createEnterSpaceHandler", () => {
    it.each([
      ["Enter", "Enter"],
      ["Space", " "],
    ])("should call handler when %s key is pressed", (_, key) => {
      const handler = vi.fn();
      const eventHandler = createEnterSpaceHandler(handler);
      const mockEvent = {
        key,
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent;

      eventHandler(mockEvent);

      expect(handler).toHaveBeenCalledTimes(1);
      expect(mockEvent.preventDefault).toHaveBeenCalledTimes(1);
    });

    it.each([
      ["a", "a"],
      ["Escape", "Escape"],
      ["Tab", "Tab"],
      ["ArrowDown", "ArrowDown"],
    ])("should not call handler when %s key is pressed", (_, key) => {
      const handler = vi.fn();
      const eventHandler = createEnterSpaceHandler(handler);
      const mockEvent = {
        key,
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent;

      eventHandler(mockEvent);

      expect(handler).not.toHaveBeenCalled();
      expect(mockEvent.preventDefault).not.toHaveBeenCalled();
    });

    it("should call handler multiple times for multiple Enter presses", () => {
      const handler = vi.fn();
      const eventHandler = createEnterSpaceHandler(handler);
      const mockEvent = {
        key: "Enter",
        preventDefault: vi.fn(),
      } as unknown as React.KeyboardEvent;

      eventHandler(mockEvent);
      eventHandler(mockEvent);
      eventHandler(mockEvent);

      expect(handler).toHaveBeenCalledTimes(3);
    });
  });
});
