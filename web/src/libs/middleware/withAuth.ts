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

import type { NextRequest, NextResponse } from "next/server";
import type { HttpClient } from "@/services/http/HttpClient";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * Request context with authenticated client.
 */
export interface RequestContext {
  /** Authenticated HTTP client. */
  client: HttpClient;
}

/**
 * Handler function that receives authenticated context.
 */
export type AuthenticatedHandler<
  T extends { [key: string]: string } = { [key: string]: string },
> = (
  ctx: RequestContext,
  request: NextRequest,
  context?: { params?: Promise<T> },
) => Promise<NextResponse>;

/**
 * Middleware wrapper that ensures authentication before calling handler.
 *
 * Parameters
 * ----------
 * handler : AuthenticatedHandler
 *     The handler function to wrap.
 *
 * Returns
 * -------
 * (request: NextRequest, context?: { params?: Promise<T> }) => Promise<NextResponse>
 *     Wrapped handler that checks authentication first.
 */
export function withAuthentication<
  T extends { [key: string]: string } = { [key: string]: string },
>(
  handler: AuthenticatedHandler<T>,
): (
  request: NextRequest,
  context?: { params?: Promise<T> },
) => Promise<NextResponse> {
  return async (request: NextRequest, context?: { params?: Promise<T> }) => {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    return handler({ client }, request, context);
  };
}
