import type { NextRequest } from "next/server";
import { BACKEND_URL } from "@/constants/config";
import type { AuthProvider } from "../auth/AuthProvider";
import { BearerAuthProvider } from "../auth/AuthProvider";

/**
 * HTTP client for making authenticated requests to the backend.
 *
 * This abstraction centralizes all backend HTTP calls, following
 * DRY, SRP, and IOC principles. It handles authentication automatically
 * and provides a clean interface for making requests.
 *
 * The client is designed to be used in Next.js API route handlers
 * (server-side only).
 */

/**
 * Options for HTTP client requests.
 */
export interface HttpClientRequestOptions {
  /**
   * HTTP method (GET, POST, PUT, DELETE, etc.).
   */
  method?: string;
  /**
   * Request headers (excluding Authorization, which is handled automatically).
   */
  headers?: HeadersInit;
  /**
   * Request body.
   */
  body?: BodyInit;
  /**
   * Query parameters to append to the URL.
   */
  queryParams?: Record<string, string | number | boolean | null | undefined>;
}

/**
 * HTTP client interface.
 *
 * Follows IOC pattern to allow for easy testing and swapping implementations.
 */
export interface HttpClient {
  /**
   * Make an authenticated request to the backend.
   *
   * Parameters
   * ----------
   * endpoint : string
   *     The backend endpoint path (e.g., "/library/artists/123").
   *     Should not include the base BACKEND_URL.
   * options : HttpClientRequestOptions
   *     Request options (method, headers, body, query params).
   *
   * Returns
   * -------
   * Promise<Response>
   *     The fetch Response object.
   */
  request(
    endpoint: string,
    options?: HttpClientRequestOptions,
  ): Promise<Response>;
}

/**
 * Default implementation of HttpClient using fetch.
 *
 * Parameters
 * ----------
 * authProvider : AuthProvider
 *     The authentication provider to use for requests.
 * baseUrl : string
 *     The base URL for the backend (defaults to BACKEND_URL).
 */
export class DefaultHttpClient implements HttpClient {
  constructor(
    private readonly authProvider: AuthProvider,
    private readonly baseUrl: string = BACKEND_URL,
  ) {}

  /**
   * Make an authenticated request to the backend.
   *
   * Parameters
   * ----------
   * endpoint : string
   *     The backend endpoint path.
   * options : HttpClientRequestOptions
   *     Request options.
   *
   * Returns
   * -------
   * Promise<Response>
   *     The fetch Response object.
   */
  async request(
    endpoint: string,
    options: HttpClientRequestOptions = {},
  ): Promise<Response> {
    const { method = "GET", headers = {}, body, queryParams } = options;

    // Build URL with query parameters
    const url = this.buildUrl(endpoint, queryParams);

    // Get authorization header from auth provider
    const authHeader = await this.authProvider.getAuthHeader();

    // Merge headers, with auth header taking precedence
    const requestHeaders: Record<string, string> = {
      ...this.normalizeHeaders(headers),
    };

    if (authHeader) {
      requestHeaders.Authorization = authHeader;
    }

    // Make the request
    return fetch(url, {
      method,
      headers: requestHeaders,
      body,
    });
  }

  /**
   * Build the full URL from endpoint and query parameters.
   *
   * Parameters
   * ----------
   * endpoint : string
   *     The endpoint path.
   * queryParams : Record<string, string | number | boolean | null | undefined> | undefined
   *     Query parameters to append.
   *
   * Returns
   * -------
   * string
   *     The full URL with query parameters.
   */
  private buildUrl(
    endpoint: string,
    queryParams?: Record<string, string | number | boolean | null | undefined>,
  ): string {
    // Ensure endpoint starts with /
    const normalizedEndpoint = endpoint.startsWith("/")
      ? endpoint
      : `/${endpoint}`;

    // Remove trailing slash from baseUrl
    const normalizedBaseUrl = this.baseUrl.replace(/\/$/, "");

    let url = `${normalizedBaseUrl}${normalizedEndpoint}`;

    // Add query parameters if provided
    if (queryParams && Object.keys(queryParams).length > 0) {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(queryParams)) {
        if (value !== null && value !== undefined) {
          searchParams.append(key, String(value));
        }
      }
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    return url;
  }

  /**
   * Normalize headers to a plain object.
   *
   * Parameters
   * ----------
   * headers : HeadersInit
   *     Headers to normalize.
   *
   * Returns
   * -------
   * Record<string, string>
   *     Normalized headers as a plain object.
   */
  private normalizeHeaders(headers: HeadersInit): Record<string, string> {
    if (headers instanceof Headers) {
      const result: Record<string, string> = {};
      headers.forEach((value, key) => {
        result[key] = value;
      });
      return result;
    }

    if (Array.isArray(headers)) {
      return Object.fromEntries(headers);
    }

    return headers as Record<string, string>;
  }
}

/**
 * Create an HTTP client from a NextRequest.
 *
 * This is a convenience function that extracts the auth token from
 * the request cookies and creates a BearerAuthProvider.
 *
 * Parameters
 * ----------
 * req : NextRequest
 *     The Next.js request object.
 * cookieName : string
 *     The name of the cookie containing the auth token.
 *
 * Returns
 * -------
 * DefaultHttpClient
 *     A configured HTTP client instance.
 */
export function createHttpClientFromRequest(
  req: NextRequest,
  cookieName: string,
): DefaultHttpClient {
  const token = req.cookies.get(cookieName)?.value;
  const authProvider = new BearerAuthProvider(token);
  return new DefaultHttpClient(authProvider);
}
