"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Eye } from "@/icons/Eye";
import { EyeSlash } from "@/icons/EyeSlash";
import styles from "./page.module.scss";

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
    <div className={styles.loginContainer}>
      <div className={styles.loginCard}>
        <div className={styles.loginHeader}>
          <h1 className={styles.loginTitle}>Sign in to Fundamental</h1>
          <p className={styles.loginSubtitle}>
            Welcome back! Please enter your details.
          </p>
        </div>

        <form onSubmit={handleSubmit} className={styles.loginForm}>
          {showPasswordChangeSuccess && (
            <output className={styles.successMessage}>
              Password changed successfully! Please sign in again to continue
              using the app.
            </output>
          )}
          {error && (
            <div className={styles.errorMessage} role="alert">
              {error}
            </div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="identifier" className={styles.label}>
              Username or Email
            </label>
            <input
              id="identifier"
              name="identifier"
              type="text"
              autoComplete="username"
              className={styles.input}
              placeholder="Enter your username or email"
              value={formData.identifier}
              onChange={handleChange}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Password
            </label>
            <div className={styles.passwordContainer}>
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                className={styles.input}
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className={styles.passwordToggle}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeSlash className={styles.eyeIcon} />
                ) : (
                  <Eye className={styles.eyeIcon} />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={styles.submitButton}
          >
            {isLoading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
