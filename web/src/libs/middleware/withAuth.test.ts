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

import { type NextRequest, NextResponse } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { HttpClient } from "@/services/http/HttpClient";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";
import { withAuthentication } from "./withAuth";

vi.mock("@/services/http/routeHelpers", () => ({
  getAuthenticatedClient: vi.fn(),
}));

/**
 * Create a mock NextRequest for testing.
 *
 * Parameters
 * ----------
 * cookies : Record<string, string>
 *     Cookie values to include in the request.
 *
 * Returns
 * -------
 * NextRequest
 *     Mock NextRequest instance.
 */
function createMockRequest(cookies: Record<string, string> = {}): NextRequest {
  return {
    cookies: {
      get: vi.fn((name: string) => {
        const value = cookies[name];
        return value ? { value } : undefined;
      }),
    },
  } as unknown as NextRequest;
}

/**
 * Create a mock HttpClient for testing.
 *
 * Returns
 * -------
 * HttpClient
 *     Mock HttpClient instance.
 */
function createMockClient(): HttpClient {
  return {
    request: vi.fn(),
  } as unknown as HttpClient;
}

/**
 * Create a mock handler for testing.
 *
 * Returns
 * -------
 * ReturnType<typeof vi.fn>
 *     Mock handler function.
 */
function createMockHandler() {
  return vi.fn(async () => NextResponse.json({ success: true }));
}

describe("withAuthentication", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should call handler with authenticated client when authentication succeeds", async () => {
    const mockClient = createMockClient();
    const mockHandler = createMockHandler();
    const mockRequest = createMockRequest({ auth_token: "test-token" });

    vi.mocked(getAuthenticatedClient).mockReturnValue({
      client: mockClient,
      error: null,
    } as ReturnType<typeof getAuthenticatedClient>);

    const wrappedHandler = withAuthentication(mockHandler);
    const result = await wrappedHandler(mockRequest);

    expect(getAuthenticatedClient).toHaveBeenCalledWith(mockRequest);
    expect(mockHandler).toHaveBeenCalledWith(
      { client: mockClient },
      mockRequest,
      undefined,
    );
    expect(result.status).toBe(200);
    const json = await result.json();
    expect(json).toEqual({ success: true });
  });

  it("should return error response when authentication fails", async () => {
    const mockHandler = createMockHandler();
    const mockRequest = createMockRequest();
    const errorResponse = NextResponse.json(
      { error: "unauthorized" },
      { status: 401 },
    );

    vi.mocked(getAuthenticatedClient).mockReturnValue({
      client: null,
      error: errorResponse,
    });

    const wrappedHandler = withAuthentication(mockHandler);
    const result = await wrappedHandler(mockRequest);

    expect(getAuthenticatedClient).toHaveBeenCalledWith(mockRequest);
    expect(mockHandler).not.toHaveBeenCalled();
    expect(result).toBe(errorResponse);
  });

  it("should pass context params to handler when provided", async () => {
    const mockClient = createMockClient();
    const mockHandler = createMockHandler();
    const mockRequest = createMockRequest({ auth_token: "test-token" });
    const mockParams = Promise.resolve({ id: "123" });
    const mockContext = { params: mockParams };

    vi.mocked(getAuthenticatedClient).mockReturnValue({
      client: mockClient,
      error: null,
    } as ReturnType<typeof getAuthenticatedClient>);

    const wrappedHandler = withAuthentication(mockHandler);
    await wrappedHandler(mockRequest, mockContext);

    expect(mockHandler).toHaveBeenCalledWith(
      { client: mockClient },
      mockRequest,
      mockContext,
    );
  });
});
