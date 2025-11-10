/**
 * Authentication provider interface for HTTP client.
 *
 * Follows IOC pattern to allow different authentication schemes
 * (Bearer, Basic, API Key, etc.) to be easily swapped.
 */

/**
 * Interface for authentication providers.
 *
 * This abstraction allows the HTTP client to support different
 * authentication schemes without being tightly coupled to any
 * specific implementation.
 */
export interface AuthProvider {
  /**
   * Get the authorization header value.
   *
   * Returns
   * -------
   * string | null
   *     The authorization header value (e.g., "Bearer token123"),
   *     or null if authentication is not available.
   */
  getAuthHeader(): Promise<string | null> | string | null;
}

/**
 * Bearer token authentication provider.
 *
 * Parameters
 * ----------
 * token : string | null | undefined
 *     The bearer token to use for authentication.
 */
export class BearerAuthProvider implements AuthProvider {
  constructor(private readonly token: string | null | undefined) {}

  /**
   * Get the Bearer authorization header.
   *
   * Returns
   * -------
   * string | null
   *     "Bearer {token}" if token exists, null otherwise.
   */
  getAuthHeader(): string | null {
    if (!this.token) {
      return null;
    }
    return `Bearer ${this.token}`;
  }
}

/**
 * Factory function to create a BearerAuthProvider from a token.
 *
 * Parameters
 * ----------
 * token : string | null | undefined
 *     The bearer token.
 *
 * Returns
 * -------
 * BearerAuthProvider
 *     A new BearerAuthProvider instance.
 */
export function createBearerAuthProvider(
  token: string | null | undefined,
): BearerAuthProvider {
  return new BearerAuthProvider(token);
}
