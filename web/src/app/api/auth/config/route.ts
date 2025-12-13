import { NextResponse } from "next/server";
import { BACKEND_URL } from "@/constants/config";

/**
 * GET /api/auth/config
 *
 * Proxy auth configuration from backend.
 */
export async function GET() {
  const response = await fetch(`${BACKEND_URL}/auth/config`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
