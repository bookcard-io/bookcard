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

/**
 * Determine whether the current request is considered secure (HTTPS).
 *
 * Next.js apps are often deployed behind a reverse proxy (e.g., nginx, Traefik,
 * Caddy). In that case, the app may receive plain HTTP traffic internally while
 * the external client connects via HTTPS. The proxy communicates this via the
 * `x-forwarded-proto` header.
 *
 * Parameters
 * ----------
 * request : NextRequest
 *     Incoming Next.js request.
 *
 * Returns
 * -------
 * boolean
 *     True when the external request is HTTPS.
 */
export function isSecureRequest(request: NextRequest): boolean {
  const forwardedProto = request.headers.get("x-forwarded-proto");
  if (forwardedProto) {
    const proto = forwardedProto.split(",")[0]?.trim().toLowerCase();
    return proto === "https";
  }
  return request.nextUrl.protocol === "https:";
}
