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
