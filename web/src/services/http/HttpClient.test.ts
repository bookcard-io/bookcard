import type { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BearerAuthProvider } from "../auth/AuthProvider";
import { createHttpClientFromRequest, DefaultHttpClient } from "./HttpClient";

describe("HttpClient", () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  let mockAuthProvider: BearerAuthProvider;

  beforeEach(() => {
    mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({}),
    });
    vi.stubGlobal("fetch", mockFetch);
    mockAuthProvider = new BearerAuthProvider("test-token");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("DefaultHttpClient", () => {
    it("should make GET request with default method", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.objectContaining({
          method: "GET",
        }),
      );
    });

    it("should use custom base URL", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://custom.test",
      );
      await client.request("/endpoint");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://custom.test/endpoint",
        expect.any(Object),
      );
    });

    it("should use BACKEND_URL as default base URL", async () => {
      const client = new DefaultHttpClient(mockAuthProvider);
      await client.request("/endpoint");

      expect(mockFetch).toHaveBeenCalled();
      const callUrl = (mockFetch.mock.calls[0] as [string, unknown])[0];
      expect(callUrl).toContain("/endpoint");
    });

    it("should make POST request with body", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      const body = JSON.stringify({ key: "value" });
      await client.request("/endpoint", {
        method: "POST",
        body,
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.objectContaining({
          method: "POST",
          body,
        }),
      );
    });

    it("should add authorization header", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
          }),
        }),
      );
    });

    it("should merge custom headers", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint", {
        headers: {
          "Content-Type": "application/json",
          "X-Custom-Header": "value",
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
            "Content-Type": "application/json",
            "X-Custom-Header": "value",
          }),
        }),
      );
    });

    it("should handle Headers object", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      const headers = new Headers();
      headers.set("X-Custom", "value");
      await client.request("/endpoint", { headers });

      expect(mockFetch).toHaveBeenCalled();
      const fetchCall = mockFetch.mock.calls[0];
      expect(fetchCall?.[0]).toBe("https://api.test/endpoint");
      const options = fetchCall?.[1] as { headers: Record<string, string> };
      expect(options?.headers).toHaveProperty(
        "Authorization",
        "Bearer test-token",
      );
      // Headers normalize keys to lowercase
      expect(options?.headers).toHaveProperty("x-custom", "value");
    });

    it("should handle headers array", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      const headers: [string, string][] = [["X-Custom", "value"]];
      await client.request("/endpoint", { headers });

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
            "X-Custom": "value",
          }),
        }),
      );
    });

    it("should add query parameters", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint", {
        queryParams: {
          key: "value",
          number: 123,
          bool: true,
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint?key=value&number=123&bool=true",
        expect.any(Object),
      );
    });

    it("should skip null and undefined query parameters", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint", {
        queryParams: {
          key: "value",
          nullValue: null,
          undefinedValue: undefined,
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint?key=value",
        expect.any(Object),
      );
    });

    it("should not add query string when all params are null/undefined", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint", {
        queryParams: {
          nullValue: null,
          undefinedValue: undefined,
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.any(Object),
      );
    });

    it("should not add query string when queryParams is empty object", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint", {
        queryParams: {},
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.any(Object),
      );
    });

    it("should normalize endpoint to start with /", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test",
      );
      await client.request("endpoint");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.any(Object),
      );
    });

    it("should remove trailing slash from base URL", async () => {
      const client = new DefaultHttpClient(
        mockAuthProvider,
        "https://api.test/",
      );
      await client.request("/endpoint");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.any(Object),
      );
    });

    it("should handle async auth provider", async () => {
      const asyncAuthProvider = {
        getAuthHeader: vi.fn().mockResolvedValue("Bearer async-token"),
      };
      const client = new DefaultHttpClient(
        asyncAuthProvider as unknown as BearerAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer async-token",
          }),
        }),
      );
    });

    it("should handle auth provider returning null", async () => {
      const nullAuthProvider = new BearerAuthProvider(null);
      const client = new DefaultHttpClient(
        nullAuthProvider,
        "https://api.test",
      );
      await client.request("/endpoint");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.test/endpoint",
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.anything(),
          }),
        }),
      );
    });
  });

  describe("createHttpClientFromRequest", () => {
    it("should create client with token from cookie", () => {
      const mockRequest = {
        cookies: {
          get: vi.fn((name: string) => {
            if (name === "test-cookie") {
              return { value: "cookie-token" };
            }
            return undefined;
          }),
        },
      } as unknown as NextRequest;

      const client = createHttpClientFromRequest(mockRequest, "test-cookie");

      expect(client).toBeInstanceOf(DefaultHttpClient);
    });

    it("should create client with undefined token when cookie not found", () => {
      const mockRequest = {
        cookies: {
          get: vi.fn(() => undefined),
        },
      } as unknown as NextRequest;

      const client = createHttpClientFromRequest(mockRequest, "test-cookie");

      expect(client).toBeInstanceOf(DefaultHttpClient);
    });
  });
});
