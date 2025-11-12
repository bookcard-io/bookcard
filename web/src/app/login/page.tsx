"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Eye } from "@/icons/Eye";
import { EyeSlash } from "@/icons/EyeSlash";

interface LoginFormData {
  identifier: string;
  password: string;
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formData, setFormData] = useState<LoginFormData>({
    identifier: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const referrer = searchParams.get("referrer");
  const showPasswordChangeSuccess = referrer === "password-change";

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          identifier: formData.identifier,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Invalid credentials");
        setIsLoading(false);
        return;
      }

      // Redirect to the next page or home
      const next = searchParams.get("next") || "/";
      router.push(next);
      router.refresh();
    } catch {
      setError("An error occurred. Please try again.");
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-[var(--color-surface-a0)] p-8 before:pointer-events-none before:absolute before:top-0 before:right-0 before:z-0 before:h-full before:w-full before:bg-[radial-gradient(ellipse_80%_60%_at_top_right,rgba(144,170,249,0.18)_0%,rgba(144,170,249,0.10)_30%,transparent_70%)] before:content-[''] after:pointer-events-none after:absolute after:top-0 after:right-0 after:z-0 after:h-full after:w-full after:bg-[linear-gradient(135deg,transparent_0%,transparent_40%,rgba(144,170,249,0.06)_60%,transparent_100%)] after:content-['']">
      <div className="relative z-[1] w-full max-w-[28rem] rounded-xl bg-[var(--color-surface-tonal-a0)] p-10 shadow-[0_4px_6px_-1px_rgba(0,0,0,0.1),0_2px_4px_-1px_rgba(0,0,0,0.06)]">
        <div className="mb-8">
          <h1 className="mb-2 font-bold text-[1.875rem] text-[var(--color-text-a0)] leading-tight">
            Sign in to Fundamental
          </h1>
          <p className="text-[var(--color-text-a30)] text-sm leading-normal">
            Welcome back! Please enter your details.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          {showPasswordChangeSuccess && (
            <output className="rounded-lg border border-[var(--color-success-a0)] bg-[var(--color-success-a20)] px-4 py-3 text-[var(--color-success-a0)] text-sm leading-normal">
              Password changed successfully! Please sign in again to continue
              using the app.
            </output>
          )}
          {error && (
            <div
              className="rounded-lg border border-[var(--color-danger-a0)] bg-[rgba(156,33,33,0.2)] px-4 py-3 text-[var(--color-danger-a20)] text-sm leading-normal"
              role="alert"
            >
              {error}
            </div>
          )}

          <div className="flex flex-col gap-2">
            <label
              htmlFor="identifier"
              className="font-medium text-[var(--color-text-a10)] text-sm leading-normal"
            >
              Username or Email
            </label>
            <input
              id="identifier"
              name="identifier"
              type="text"
              autoComplete="username"
              className="w-full rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] px-4 py-3 text-[var(--color-text-a0)] text-base leading-normal transition-[border-color,box-shadow] duration-200 placeholder:text-[var(--color-text-a40)] focus:border-[var(--color-primary-a0)] focus:shadow-[0_0_0_3px_rgba(144,170,249,0.1)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Enter your username or email"
              value={formData.identifier}
              onChange={handleChange}
              required
            />
          </div>

          <div className="flex flex-col gap-2">
            <label
              htmlFor="password"
              className="font-medium text-[var(--color-text-a10)] text-sm leading-normal"
            >
              Password
            </label>
            <div className="relative flex items-center">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                className="w-full rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] px-4 py-3 pr-12 text-[var(--color-text-a0)] text-base leading-normal transition-[border-color,box-shadow] duration-200 placeholder:text-[var(--color-text-a40)] focus:border-[var(--color-primary-a0)] focus:shadow-[0_0_0_3px_rgba(144,170,249,0.1)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 flex cursor-pointer items-center justify-center border-none bg-transparent p-1 text-[var(--color-text-a30)] transition-colors duration-200 hover:text-[var(--color-text-a10)] focus:text-[var(--color-primary-a0)] focus:outline-none"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeSlash className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full cursor-pointer rounded-lg border-none bg-[var(--color-primary-a0)] px-4 py-3 font-medium text-[var(--color-surface-a20)] text-base leading-normal transition-[background-color,opacity] duration-200 hover:bg-[var(--color-primary-a10)] focus:shadow-[0_0_0_3px_rgba(144,170,249,0.3)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 hover:disabled:bg-[var(--color-primary-a0)]"
          >
            {isLoading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
