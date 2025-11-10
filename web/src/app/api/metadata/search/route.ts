import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/metadata/search
 *
 * Proxies request to search for book metadata from external sources.
 * Supports query parameters: query, locale, max_results_per_provider, provider_ids
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { searchParams } = request.nextUrl;
    const query = searchParams.get("query");

    if (!query) {
      return NextResponse.json(
        { detail: "Query parameter is required" },
        { status: 400 },
      );
    }

    const queryParams: Record<string, string> = { query };
    const locale = searchParams.get("locale");
    if (locale) {
      queryParams.locale = locale;
    }

    const maxResults = searchParams.get("max_results_per_provider");
    if (maxResults) {
      queryParams.max_results_per_provider = maxResults;
    }

    const providerIds = searchParams.get("provider_ids");
    if (providerIds) {
      queryParams.provider_ids = providerIds;
    }

    const response = await client.request("/metadata/search", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to search metadata" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * POST /api/metadata/search
 *
 * Proxies request to search for book metadata from external sources.
 * Accepts JSON body with query, locale, max_results_per_provider, provider_ids
 */
export async function POST(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const body = await request.json();

    if (!body.query) {
      return NextResponse.json(
        { detail: "Query is required" },
        { status: 400 },
      );
    }

    const response = await client.request("/metadata/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to search metadata" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
