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

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import type { vi } from "vitest";
import type { Library } from "@/contexts/ActiveLibraryContext";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { UserProvider } from "@/contexts/UserContext";

/**
 * Creates a QueryClient for testing with default options.
 *
 * Returns
 * -------
 * QueryClient
 *     QueryClient instance configured for testing.
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
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
}

/**
 * Creates a wrapper component with QueryClientProvider and ActiveLibraryProvider for testing React Query hooks.
 *
 * Parameters
 * ----------
 * queryClient : QueryClient | undefined
 *     Optional QueryClient instance. If not provided, creates a new one.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
export function createQueryClientWrapper(
  queryClient?: QueryClient,
): ({ children }: { children: ReactNode }) => React.JSX.Element {
  const client = queryClient ?? createTestQueryClient();
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>
      <UserProvider>
        <ActiveLibraryProvider>{children}</ActiveLibraryProvider>
      </UserProvider>
    </QueryClientProvider>
  );
}

/**
 * Provider endpoints that are called automatically by UserProvider and ActiveLibraryProvider.
 * These should be excluded when checking fetch call counts in tests.
 */
const PROVIDER_ENDPOINTS = [
  "/api/auth/me",
  "/api/auth/settings",
  "/api/libraries/active",
];

/**
 * Filters out provider-related fetch calls from mock call history.
 *
 * Parameters
 * ----------
 * fetchMock : ReturnType<typeof vi.fn>
 *     The mocked fetch function.
 *
 * Returns
 * -------
 * Array<unknown[]>
 *     Array of fetch calls excluding provider endpoints.
 *
 * Examples
 * --------
 * ```ts
 * const nonProviderCalls = getNonProviderFetchCalls(globalThis.fetch as ReturnType<typeof vi.fn>);
 * expect(nonProviderCalls).toHaveLength(1);
 * ```
 */
export function getNonProviderFetchCalls(
  fetchMock: ReturnType<typeof vi.fn>,
): unknown[][] {
  return fetchMock.mock.calls.filter(
    (call) =>
      typeof call[0] === "string" &&
      !PROVIDER_ENDPOINTS.some((endpoint) => call[0] === endpoint),
  );
}

/**
 * Default mock active library for tests.
 */
export const mockActiveLibrary: Library = {
  id: 1,
  name: "Test Library",
  calibre_db_path: "/path/to/library",
  calibre_db_file: "metadata.db",
  calibre_uuid: null,
  use_split_library: false,
  split_library_dir: null,
  auto_reconnect: false,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

type MockResponse = { ok: boolean; json: () => Promise<unknown> };
type UrlMatcher = string | ((url: string) => boolean);
type MockResponseConfig =
  | MockResponse
  | { matcher: UrlMatcher; response: MockResponse };

/**
 * Creates a mock fetch implementation that automatically handles active library requests.
 *
 * This fixture eliminates DRY violations by centralizing the active library mock logic.
 * All fetch mocks in tests should use this helper to ensure consistency.
 *
 * Parameters
 * ----------
 * responses : Array<MockResponse | MockResponseConfig>
 *     Array of mock responses for non-active-library requests. Can be:
 *     - Simple response objects (returned in order for sequential fetch calls)
 *     - Objects with `matcher` (URL string or function) and `response` for pattern matching
 * activeLibrary : Library | undefined
 *     Optional active library to return. Defaults to mockActiveLibrary.
 *
 * Returns
 * -------
 * (url: string) => Promise<Response>
 *     Mock fetch implementation that handles active library and other requests.
 *
 * Examples
 * --------
 * ```ts
 * // Simple sequential responses
 * const mockResponse = { ok: true, json: () => Promise.resolve(data) };
 * (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
 *   createMockFetchWithActiveLibrary(mockResponse)
 * );
 *
 * // URL pattern matching
 * (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
 *   createMockFetchWithActiveLibrary(
 *     { matcher: (url) => url.includes("/api/books/"), response: bookResponse },
 *     mockListResponse
 *   )
 * );
 * ```
 */
export function createMockFetchWithActiveLibrary(
  ...responses: Array<MockResponse | MockResponseConfig>
): (url: string) => Promise<Response>;
export function createMockFetchWithActiveLibrary(
  activeLibrary: Library,
  ...responses: Array<MockResponse | MockResponseConfig>
): (url: string) => Promise<Response>;
export function createMockFetchWithActiveLibrary(
  activeLibraryOrResponse?: Library | MockResponse | MockResponseConfig,
  ...responses: Array<MockResponse | MockResponseConfig>
): (url: string) => Promise<Response> {
  // Check if first argument is a Library (has is_active property)
  const isLibrary = (
    arg: Library | MockResponse | MockResponseConfig | undefined,
  ): arg is Library => {
    return arg !== undefined && typeof arg === "object" && "is_active" in arg;
  };

  const activeLibrary = isLibrary(activeLibraryOrResponse)
    ? activeLibraryOrResponse
    : mockActiveLibrary;
  const allResponses: Array<MockResponse | MockResponseConfig> = isLibrary(
    activeLibraryOrResponse,
  )
    ? responses
    : activeLibraryOrResponse !== undefined
      ? [activeLibraryOrResponse, ...responses]
      : responses;

  let responseIndex = 0;
  return (url: string) => {
    // Handle active library endpoint
    if (url === "/api/libraries/active") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(activeLibrary),
      } as Response);
    }

    // Handle user profile endpoint (required by UserProvider)
    if (url === "/api/auth/me") {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            id: 1,
            username: "testuser",
            email: "test@example.com",
            ereader_devices: [],
          }),
      } as Response);
    }

    // Handle user settings endpoint (required by UserProvider)
    if (url === "/api/auth/settings") {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ settings: {} }),
      } as Response);
    }

    // Check URL matchers first (pattern matching)
    for (const config of allResponses) {
      if (
        typeof config === "object" &&
        "matcher" in config &&
        "response" in config
      ) {
        const matches =
          typeof config.matcher === "string"
            ? url === config.matcher
            : config.matcher(url);
        if (matches) {
          return Promise.resolve(config.response as Response);
        }
      }
    }

    // Fall back to sequential responses (simple responses without matchers)
    const simpleResponses = allResponses.filter(
      (r): r is MockResponse =>
        typeof r === "object" && !("matcher" in r) && "ok" in r,
    );
    if (responseIndex < simpleResponses.length) {
      const response = simpleResponses[responseIndex];
      responseIndex++;
      return Promise.resolve(response as Response);
    }

    return Promise.reject(new Error(`Unexpected fetch to ${url}`));
  };
}
