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

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { scrollToProviderResults } from "./metadataScroll";

describe("metadataScroll utils", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.body.innerHTML = "";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("scrollToProviderResults", () => {
    it("should scroll to results section when it exists", () => {
      const resultsSection = document.createElement("div");
      resultsSection.id = "metadata-results-section";
      document.body.appendChild(resultsSection);

      const scrollIntoViewSpy = vi.spyOn(resultsSection, "scrollIntoView");

      scrollToProviderResults("Test Provider");

      expect(scrollIntoViewSpy).toHaveBeenCalledWith({
        behavior: "smooth",
        block: "start",
      });
    });

    it("should not throw when results section does not exist", () => {
      expect(() => {
        scrollToProviderResults("Test Provider");
      }).not.toThrow();
    });

    it("should schedule scroll to provider result element", () => {
      const resultsSection = document.createElement("div");
      resultsSection.id = "metadata-results-section";
      document.body.appendChild(resultsSection);

      const resultElement = document.createElement("div");
      resultElement.id = "result-test-provider";
      document.body.appendChild(resultElement);

      const scrollIntoViewSpy = vi.spyOn(resultElement, "scrollIntoView");
      const setTimeoutCalls: Array<[() => void, number]> = [];
      vi.stubGlobal("setTimeout", (callback: () => void, delay: number) => {
        setTimeoutCalls.push([callback, delay]);
        callback();
        return 1;
      });

      scrollToProviderResults("Test Provider");

      expect(setTimeoutCalls).toHaveLength(1);
      expect(setTimeoutCalls[0]?.[1]).toBe(100);
      expect(scrollIntoViewSpy).toHaveBeenCalledWith({
        behavior: "smooth",
        block: "start",
      });
    });

    it("should normalize provider name to create element ID", () => {
      const resultsSection = document.createElement("div");
      resultsSection.id = "metadata-results-section";
      document.body.appendChild(resultsSection);

      const resultElement = document.createElement("div");
      resultElement.id = "result-test-provider-name";
      document.body.appendChild(resultElement);

      const scrollIntoViewSpy = vi.spyOn(resultElement, "scrollIntoView");
      vi.stubGlobal("setTimeout", (callback: () => void) => {
        callback();
        return 1;
      });

      scrollToProviderResults("Test Provider Name");

      expect(scrollIntoViewSpy).toHaveBeenCalled();
    });

    it("should handle provider name with multiple spaces", () => {
      const resultsSection = document.createElement("div");
      resultsSection.id = "metadata-results-section";
      document.body.appendChild(resultsSection);

      const resultElement = document.createElement("div");
      resultElement.id = "result-test-provider-with-spaces";
      document.body.appendChild(resultElement);

      const scrollIntoViewSpy = vi.spyOn(resultElement, "scrollIntoView");
      vi.stubGlobal("setTimeout", (callback: () => void) => {
        callback();
        return 1;
      });

      scrollToProviderResults("Test  Provider  With  Spaces");

      expect(scrollIntoViewSpy).toHaveBeenCalled();
    });

    it("should not throw when provider result element does not exist", () => {
      const resultsSection = document.createElement("div");
      resultsSection.id = "metadata-results-section";
      document.body.appendChild(resultsSection);

      vi.stubGlobal("setTimeout", (callback: () => void) => {
        callback();
        return 1;
      });

      expect(() => {
        scrollToProviderResults("Non Existent Provider");
      }).not.toThrow();
    });
  });
});
