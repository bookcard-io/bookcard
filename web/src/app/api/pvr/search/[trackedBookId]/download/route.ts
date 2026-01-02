import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * POST /api/pvr/search/[trackedBookId]/download
 *
 * Proxies POST request to backend PVR search download endpoint.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ trackedBookId: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { trackedBookId } = await params;
    const backendPath = `/pvr/search/${trackedBookId}/download`;

    // Read request body
    const body = await request.text();

    const response = await client.request(backendPath, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body,
    });

    if (!response.ok) {
      try {
        const errorData = await response.json();
        return NextResponse.json(errorData, { status: response.status });
      } catch {
        return NextResponse.json(
          { detail: "Failed to initiate download" },
          { status: response.status },
        );
      }
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("PVR download proxy error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
