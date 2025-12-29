import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * POST /api/download-clients/[id]/test
 * Test connection to a download client.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) {
      return error;
    }

    const { id } = await params;
    const response = await client.request(`/download-clients/${id}/test`, {
      method: "POST",
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Connection test failed" },
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
