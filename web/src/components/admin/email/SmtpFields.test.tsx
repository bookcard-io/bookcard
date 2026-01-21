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

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { EmailServerConfigFormData } from "@/hooks/useEmailServerConfig";
import { SmtpFields } from "./SmtpFields";

// Helper to create default form data
const createFormData = (
  overrides: Partial<EmailServerConfigFormData> = {},
): EmailServerConfigFormData => ({
  server_type: "smtp",
  smtp_host: "smtp.example.com",
  smtp_port: 587,
  smtp_username: "user@example.com",
  smtp_password: undefined,
  smtp_use_tls: true,
  smtp_use_ssl: false,
  smtp_from_email: "sender@example.com",
  smtp_from_name: "Sender",
  max_email_size_mb: 25,
  gmail_token: null,
  enabled: true,
  ...overrides,
});

describe("SmtpFields", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders all SMTP fields", () => {
    const formData = createFormData();
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    expect(screen.getByLabelText("SMTP Host")).toBeInTheDocument();
    expect(screen.getByLabelText("SMTP Port")).toBeInTheDocument();
    expect(screen.getByLabelText("Max Email Size (MB)")).toBeInTheDocument();
    expect(screen.getByLabelText("SMTP Username")).toBeInTheDocument();
    expect(screen.getByLabelText("SMTP Password")).toBeInTheDocument();
    expect(screen.getByLabelText("TLS")).toBeInTheDocument();
    expect(screen.getByLabelText("SSL")).toBeInTheDocument();
    expect(screen.getByLabelText("From Email")).toBeInTheDocument();
  });

  it("calls onFieldChange when password input changes", () => {
    const formData = createFormData();
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const passwordInput = screen.getByLabelText("SMTP Password");
    fireEvent.change(passwordInput, { target: { value: "newpassword" } });

    expect(onFieldChange).toHaveBeenCalledWith("smtp_password", "newpassword");
  });

  it("calls onFieldChange with empty string when password is cleared", () => {
    const formData = createFormData({ smtp_password: "oldpassword" });
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const passwordInput = screen.getByLabelText("SMTP Password");
    fireEvent.change(passwordInput, { target: { value: "" } });

    expect(onFieldChange).toHaveBeenCalledWith("smtp_password", "");
  });

  it("renders password field with value when provided", () => {
    const formData = createFormData({ smtp_password: "existingpassword" });
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const passwordInput = screen.getByLabelText(
      "SMTP Password",
    ) as HTMLInputElement;
    expect(passwordInput.value).toBe("existingpassword");
  });

  it("renders empty password field when value is undefined", () => {
    const formData = createFormData({ smtp_password: undefined });
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const passwordInput = screen.getByLabelText(
      "SMTP Password",
    ) as HTMLInputElement;
    expect(passwordInput.value).toBe("");
  });

  it("renders placeholder for password field", () => {
    const formData = createFormData();
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const passwordInput = screen.getByLabelText("SMTP Password");
    expect(passwordInput).toHaveAttribute(
      "placeholder",
      "Password (leave blank for no authentication)",
    );
  });

  it("shows From Email as required when username is empty", () => {
    const formData = createFormData({ smtp_username: null });
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const fromEmailInput = screen.getByLabelText("From Email *");
    expect(fromEmailInput).toBeRequired();
    expect(
      screen.getByText("Required when no username is provided"),
    ).toBeInTheDocument();
  });

  it("does not show From Email as required when username is provided", () => {
    const formData = createFormData({ smtp_username: "user" });
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const fromEmailInput = screen.getByLabelText("From Email");
    expect(fromEmailInput).not.toBeRequired();
    expect(
      screen.queryByText("Required when no username is provided"),
    ).not.toBeInTheDocument();
  });

  it("calls onFieldChange with empty string when username is cleared", () => {
    const formData = createFormData({ smtp_username: "existing_user" });
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const usernameInput = screen.getByLabelText("SMTP Username");
    fireEvent.change(usernameInput, { target: { value: "" } });

    expect(onFieldChange).toHaveBeenCalledWith("smtp_username", "");
  });

  it("renders placeholder for username field", () => {
    const formData = createFormData();
    const onFieldChange = vi.fn();

    render(<SmtpFields formData={formData} onFieldChange={onFieldChange} />);

    const usernameInput = screen.getByLabelText("SMTP Username");
    expect(usernameInput).toHaveAttribute(
      "placeholder",
      "Username (leave blank for no authentication)",
    );
  });
});
