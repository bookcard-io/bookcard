import type { NextRequest } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

/**
 * GET /api/metadata/search/stream
 *
 * Proxies SSE stream for live metadata search progress.
 * Query params: query, locale, max_results_per_provider, provider_ids, request_id
 */
export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return new Response(JSON.stringify({ detail: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
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

  const url = new URL(`${BACKEND_URL}/metadata/search/stream`);
  url.searchParams.set("query", query);
  const locale = searchParams.get("locale");
  if (locale) url.searchParams.set("locale", locale);
  const maxResults = searchParams.get("max_results_per_provider");
  if (maxResults) url.searchParams.set("max_results_per_provider", maxResults);
  const providerIds = searchParams.get("provider_ids");
  if (providerIds) url.searchParams.set("provider_ids", providerIds);
  const requestId = searchParams.get("request_id");
  if (requestId) url.searchParams.set("request_id", requestId);

  // Connect to backend SSE
  const backendResponse = await fetch(url.toString(), {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "text/event-stream",
    },
    signal: request.signal,
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
  const stream = new ReadableStream({
    start(controller) {
      const reader = backendResponse.body?.getReader();
      if (!reader) {
        controller.close();
        return;
      }
      const pump = (): Promise<void> =>
        reader.read().then(({ done, value }) => {
          if (done) {
            controller.close();
            return Promise.resolve();
          }
          if (value) controller.enqueue(value);
          return pump();
        });
      pump().catch(() => {
        try {
          controller.close();
        } catch {
          // ignore
        }
      });
    },
    cancel() {
      try {
        backendResponse.body?.cancel();
      } catch {
        // ignore
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
