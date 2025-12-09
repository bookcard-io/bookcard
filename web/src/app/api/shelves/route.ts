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
import { UnsupportedContentTypeError } from "@/libs/errors";
import { withAuthentication } from "@/libs/middleware/withAuth";
import {
  parseShelfCreationFormData,
  parseShelfCreationJson,
} from "@/libs/request/parsers";
import { err } from "@/libs/result";
import { HttpShelfRepository } from "@/services/shelf/shelfRepository";
import { ShelfService } from "@/services/shelf/shelfService";

/**
 * GET /api/shelves
 *
 * Proxies request to list shelves from the active library.
 */
export const GET = withAuthentication(async (ctx, _request) => {
  const repository = new HttpShelfRepository(ctx.client);
  const service = new ShelfService(repository);

  const result = await service.list();

  return result.match({
    ok: (shelves) => NextResponse.json(shelves),
    err: (error) => (error as ApiError).toResponse(),
  });
});

/**
 * POST /api/shelves
 *
 * Proxies request to create a new shelf.
 *
 * Supports two request types:
 * - application/json: simple shelf creation
 * - multipart/form-data: shelf creation with optional read list file
 */
export const POST = withAuthentication(async (ctx, request) => {
  const contentType = request.headers.get("content-type") || "";

  // JSON payload: simple shelf creation
  if (contentType.startsWith("application/json")) {
    const input = await parseShelfCreationJson(request);

    if (input.isErr) {
      return input.error.toResponse();
    }

    const repository = new HttpShelfRepository(ctx.client);
    const service = new ShelfService(repository);

    const result = await service.create(input.value);

    return result.match({
      ok: (shelf) => NextResponse.json(shelf),
      err: (error) => (error as ApiError).toResponse(),
    });
  }

  // Multipart payload: shelf creation with optional read list file
  if (contentType.startsWith("multipart/form-data")) {
    const formData = await request.formData();
    const input = parseShelfCreationFormData(formData);

    if (input.isErr) {
      return input.error.toResponse();
    }

    const repository = new HttpShelfRepository(ctx.client);
    const service = new ShelfService(repository);

    const result = await service.createWithImport(
      input.value.shelf,
      input.value.file,
      input.value.importOptions,
    );

    return result.match({
      ok: (shelf) => NextResponse.json(shelf),
      err: (error) => (error as ApiError).toResponse(),
    });
  }

  // Unsupported content type
  return err(
    new UnsupportedContentTypeError("Unsupported content type"),
  ).error.toResponse();
});
