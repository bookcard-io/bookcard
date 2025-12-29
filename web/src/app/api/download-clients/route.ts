import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/download-clients
 * List all download clients.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) {
      return error;
    }

    const { searchParams } = request.nextUrl;
    const enabledOnly = searchParams.get("enabled_only") === "true";

    const response = await client.request("/download-clients", {
      method: "GET",
      queryParams: enabledOnly ? { enabled_only: "true" } : undefined,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch download clients" },
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
 * POST /api/download-clients
 * Create a new download client.
 */
export async function POST(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) {
      return error;
    }

    const body = await request.json();

    const response = await client.request("/download-clients", {
      method: "POST",
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to create download client" },
        { status: response.status },
      );
    }

    return NextResponse.json(data, { status: 201 });
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
