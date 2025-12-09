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
import type { ApiError } from "@/libs/errors";
import { withAuthentication } from "@/libs/middleware/withAuth";
import { parseIdParam, parseImportFormData } from "@/libs/request/parsers";
import { HttpShelfRepository } from "@/services/shelf/shelfRepository";
import { ShelfService } from "@/services/shelf/shelfService";

/**
 * POST /api/shelves/[id]/import
 *
 * Proxies request to import a read list file into a shelf.
 */
export const POST = withAuthentication<{ id: string }>(
  async (ctx, request, context) => {
    const params = context?.params;
    if (!params) {
      return NextResponse.json(
        { detail: "Missing route parameters" },
        { status: 400 },
      );
    }

    // Parse shelf ID from route params
    const shelfIdResult = await parseIdParam(params, "id");

    if (shelfIdResult.isErr) {
      return shelfIdResult.error.toResponse();
    }

    // Read formData first before any other request access
    // to avoid "body already consumed" errors in Next.js
    const formData = await request.formData();
    const input = parseImportFormData(formData);

    if (input.isErr) {
      return input.error.toResponse();
    }

    const repository = new HttpShelfRepository(ctx.client);
    const service = new ShelfService(repository);

    const result = await service.importReadList(
      shelfIdResult.value,
      input.value.file,
      input.value.options,
    );

    return result.match({
      ok: (data) => NextResponse.json(data),
      err: (error) => (error as ApiError).toResponse(),
    });
  },
);
