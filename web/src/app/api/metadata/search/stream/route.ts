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
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/metadata/search/stream
 *
 * Proxies SSE stream for live metadata search progress.
 * Query params: query, locale, max_results_per_provider, provider_ids, enable_providers, request_id
 */
export async function GET(request: NextRequest) {
  const { client, error } = getAuthenticatedClient(request);
  if (error) {
    return error;
  }

  const { searchParams } = request.nextUrl;
  const query = searchParams.get("query");
  if (!query) {
    return new Response(
      JSON.stringify({ detail: "Query parameter is required" }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  const queryParams: Record<string, string> = { query };
  const locale = searchParams.get("locale");
  if (locale) queryParams.locale = locale;
  const maxResults = searchParams.get("max_results_per_provider");
  if (maxResults) queryParams.max_results_per_provider = maxResults;
  const providerIds = searchParams.get("provider_ids");
  if (providerIds) queryParams.provider_ids = providerIds;
  const enableProviders = searchParams.get("enable_providers");
  if (enableProviders) queryParams.enable_providers = enableProviders;
  const requestId = searchParams.get("request_id");
  if (requestId) queryParams.request_id = requestId;

  // Connect to backend SSE
  const backendResponse = await client.request("/metadata/search/stream", {
    method: "GET",
    headers: {
      Accept: "text/event-stream",
    },
    queryParams,
  });

  if (!backendResponse.ok || backendResponse.body == null) {
    const detail = await backendResponse
      .text()
      .catch(() => "Failed to open stream");
    return new Response(JSON.stringify({ detail }), {
      status: backendResponse.status || 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Pipe backend SSE to client
  let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  const stream = new ReadableStream({
    start(controller) {
      reader = backendResponse.body?.getReader() ?? null;
      if (!reader) {
        controller.close();
        return;
      }
      const pump = (): Promise<void> => {
        if (!reader) {
          return Promise.resolve();
        }
        return reader.read().then(({ done, value }) => {
          if (done) {
            controller.close();
            return Promise.resolve();
          }
          if (value) controller.enqueue(value);
          return pump();
        });
      };
      pump().catch(() => {
        try {
          controller.close();
        } catch {
          // ignore
        }
      });
    },
    cancel() {
      // Cancel the reader instead of the stream, since the stream is locked once we get a reader
      if (reader) {
        reader.cancel().catch(() => {
          // ignore cancellation errors
        });
      } else if (backendResponse.body && !backendResponse.body.locked) {
        // Only try to cancel the stream if it's not locked and we don't have a reader
        try {
          backendResponse.body.cancel().catch(() => {
            // ignore cancellation errors
          });
        } catch {
          // ignore
        }
      }
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
