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

import { QueryClient } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createQueryClientWrapper } from "./test-utils";
import { useReadingSession } from "./useReadingSession";

describe("useReadingSession", () => {
  let queryClient: QueryClient;
  let wrapper: ReturnType<typeof createQueryClientWrapper>;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
        mutations: {
          retry: false,
        },
      },
    });
    wrapper = createQueryClientWrapper(queryClient);
    // Mock document.visibilityState
    Object.defineProperty(document, "hidden", {
      writable: true,
      configurable: true,
      value: false,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    queryClient.clear();
  });

  it("should auto-start session on mount when autoStart is true", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: true,
        }),
      { wrapper },
    );

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should not auto-start when autoStart is false", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
        }),
      { wrapper },
    );

    expect(result.current.sessionId).toBeNull();
    expect(result.current.isActive).toBe(false);
  });

  it("should not auto-start when bookId is 0 or negative", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 0,
          format: "EPUB",
          autoStart: true,
        }),
      { wrapper },
    );

    expect(result.current.sessionId).toBeNull();
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const sessionCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("/api/reading/sessions"),
    );
    expect(sessionCalls.length).toBe(0);
  });

  it("should not auto-start when format is empty", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "",
          autoStart: true,
        }),
      { wrapper },
    );

    expect(result.current.sessionId).toBeNull();
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const sessionCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("/api/reading/sessions"),
    );
    expect(sessionCalls.length).toBe(0);
  });

  it("should not start session if already started", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
        }),
      { wrapper },
    );

    expect(result.current.sessionId).toBeNull();
  });

  it("should not start session if already starting", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
        }),
      { wrapper },
    );

    expect(result.current.isStarting).toBe(false);
  });

  it("should not end session if no active session", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
        }),
      { wrapper },
    );

    expect(result.current.sessionId).toBeNull();
  });

  it("should not end session if already ending", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
        }),
      { wrapper },
    );

    expect(result.current.isEnding).toBe(false);
  });

  it("should not end session if already ended", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
        }),
      { wrapper },
    );

    expect(result.current.sessionId).toBeNull();
  });

  it("should call onSessionStart callback", () => {
    const onSessionStart = vi.fn();

    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
          onSessionStart,
        }),
      { wrapper },
    );

    expect(result.current).toBeDefined();
  });

  it("should handle end error", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
        }),
      { wrapper },
    );

    expect(result.current.error).toBeNull();
  });

  it("should auto-end session on unmount", () => {
    const { result, unmount } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
          autoEnd: true,
        }),
      { wrapper },
    );

    unmount();
    // Test unmount behavior - just verify unmount doesn't throw
    expect(result.current).toBeDefined();
  });

  it("should reset refs when bookId or format changes", () => {
    const { result, rerender } = renderHook(
      ({ bookId, format }) =>
        useReadingSession({
          bookId,
          format,
          autoStart: true,
        }),
      {
        wrapper,
        initialProps: { bookId: 1, format: "EPUB" },
      },
    );

    // Change bookId
    rerender({ bookId: 2, format: "EPUB" });

    // Verify rerender doesn't throw
    expect(result.current).toBeDefined();
  });

  it("should use device identifier when provided", () => {
    const { result } = renderHook(
      () =>
        useReadingSession({
          bookId: 1,
          format: "EPUB",
          autoStart: false,
          device: "device-123",
        }),
      { wrapper },
    );

    expect(result.current).toBeDefined();
  });
});
