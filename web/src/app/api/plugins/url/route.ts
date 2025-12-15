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

import { NextResponse } from "next/server";
import { withAuthentication } from "@/libs/middleware/withAuth";

/**
 * POST /api/plugins/url
 *
 * Proxies request to install a plugin from a URL (downloads ZIP).
 */
export const POST = withAuthentication<Record<string, never>>(
  async (ctx, request) => {
    try {
      const body = await request.json();

      const response = await ctx.client.request("/plugins/url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          { detail: data.detail || "Failed to install plugin from URL" },
          { status: response.status },
        );
      }

      return NextResponse.json(data, { status: response.status });
    } catch (error) {
      console.error("Error in POST /api/plugins/url:", error);
      return NextResponse.json(
        { detail: "Internal server error" },
        { status: 500 },
      );
    }
  },
);
