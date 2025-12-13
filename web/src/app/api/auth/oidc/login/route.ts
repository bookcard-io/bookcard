import { type NextRequest, NextResponse } from "next/server";
import { BACKEND_URL } from "@/constants/config";

const POST_LOGIN_NEXT_COOKIE = "fundamental_post_login_next";

/**
 * GET /api/auth/oidc/login
 *
 * Starts OIDC login by redirecting to backend /auth/oidc/login.
 * Stores the desired post-login path in a short-lived, httpOnly cookie.
 */
export async function GET(request: NextRequest) {
  const next = request.nextUrl.searchParams.get("next") || "/";
  const redirectUri = `${request.nextUrl.origin}/api/auth/oidc/callback`;

  const backendLoginUrl = new URL(`${BACKEND_URL}/auth/oidc/login`);
  backendLoginUrl.searchParams.set("redirect_uri", redirectUri);
  backendLoginUrl.searchParams.set("next", next);

  const response = NextResponse.redirect(backendLoginUrl.toString(), 302);
  response.cookies.set(POST_LOGIN_NEXT_COOKIE, next, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 10 * 60,
  });
  return response;
}
