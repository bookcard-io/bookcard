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

import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { describe, expect, it, vi } from "vitest";
import { AUTH_COOKIE_NAME } from "@/constants/config";
import { getAuthenticatedClient } from "./routeHelpers";

describe("routeHelpers", () => {
  describe("getAuthenticatedClient", () => {
    it("should return client when token exists", () => {
      const mockRequest = {
        cookies: {
          get: vi.fn((name: string) => {
            if (name === AUTH_COOKIE_NAME) {
              return { value: "test-token" };
            }
            return undefined;
          }),
        },
      } as unknown as NextRequest;

      const result = getAuthenticatedClient(mockRequest);

      expect(result.client).not.toBeNull();
      expect(result.error).toBeNull();
    });

    it("should return error when token is missing", () => {
      const mockRequest = {
        cookies: {
          get: vi.fn(() => undefined),
        },
      } as unknown as NextRequest;

      const result = getAuthenticatedClient(mockRequest);

      expect(result.client).toBeNull();
      expect(result.error).toBeInstanceOf(NextResponse);
      expect(result.error?.status).toBe(401);
    });

    it("should return error when token is null", () => {
      const mockRequest = {
        cookies: {
          get: vi.fn(() => ({ value: null })),
        },
      } as unknown as NextRequest;

      const result = getAuthenticatedClient(mockRequest);

      expect(result.client).toBeNull();
      expect(result.error).toBeInstanceOf(NextResponse);
      expect(result.error?.status).toBe(401);
    });

    it("should return error when token is empty string", () => {
      const mockRequest = {
        cookies: {
          get: vi.fn(() => ({ value: "" })),
        },
      } as unknown as NextRequest;

      const result = getAuthenticatedClient(mockRequest);

      expect(result.client).toBeNull();
      expect(result.error).toBeInstanceOf(NextResponse);
      expect(result.error?.status).toBe(401);
    });

    it("should use AUTH_COOKIE_NAME for cookie lookup", () => {
      const mockGet = vi.fn((name: string) => {
        if (name === AUTH_COOKIE_NAME) {
          return { value: "test-token" };
        }
        return undefined;
      });
      const mockRequest = {
        cookies: {
          get: mockGet,
        },
      } as unknown as NextRequest;

      getAuthenticatedClient(mockRequest);

      expect(mockGet).toHaveBeenCalledWith(AUTH_COOKIE_NAME);
    });
  });
});
