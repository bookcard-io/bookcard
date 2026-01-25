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
import { ScheduledTasksConfig } from "./ScheduledTasksConfig";

// Mock hooks
const mockUpdateJob = vi.fn();
const mockUpdateField = vi.fn();

vi.mock("@/hooks/useScheduledJobs", () => ({
  useScheduledJobs: () => ({
    jobs: [
      {
        job_name: "test_job_1",
        description: "Test Job 1",
        task_type: "metadata_backup",
        cron_expression: "0 0 * * *",
        enabled: true,
        last_run_at: "2023-01-01T12:00:00Z",
        last_run_status: "completed",
      },
      {
        job_name: "test_job_2",
        description: null,
        task_type: "library_scan",
        cron_expression: "0 1 * * *",
        enabled: false,
        last_run_at: null,
        last_run_status: null,
      },
    ],
    isLoading: false,
    isSaving: false,
    error: null,
    updateJob: mockUpdateJob,
  }),
}));

vi.mock("@/hooks/useScheduledTasksConfig", () => ({
  useScheduledTasksConfig: () => ({
    config: {
      duration_hours: 10,
    },
    isLoading: false,
    isSaving: false,
    error: null,
    updateField: mockUpdateField,
  }),
}));

vi.mock("@/components/profile/BlurAfterClickContext", () => ({
  useBlurAfterClick: () => ({
    onBlurChange: (fn: unknown) => fn,
  }),
}));

describe("ScheduledTasksConfig", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders scheduled tasks list", () => {
    render(<ScheduledTasksConfig />);

    expect(
      screen.getByText("Scheduled Tasks Configuration"),
    ).toBeInTheDocument();
    expect(screen.getByText("Test Job 1")).toBeInTheDocument();
    expect(screen.getByText("Test Job 2")).toBeInTheDocument(); // Formatted title
  });

  it("renders last run info correctly", () => {
    render(<ScheduledTasksConfig />);

    // Job 1 has last run info
    expect(screen.getByText("completed")).toBeInTheDocument();
    // Check for date formatting (locale dependent, so just check it exists)
    expect(screen.getByText(/Last run:/)).toBeInTheDocument();
  });

  it("calls updateJob when toggling enabled status", () => {
    render(<ScheduledTasksConfig />);

    // Find checkboxes (there are 2)
    const checkboxes = screen.getAllByRole("checkbox");

    // Toggle the first one (enabled -> disabled)
    const checkbox1 = checkboxes[0];
    expect(checkbox1).toBeDefined();
    if (checkbox1) {
      fireEvent.click(checkbox1);
      expect(mockUpdateJob).toHaveBeenCalledWith("test_job_1", {
        enabled: false,
      });
    }

    // Toggle the second one (disabled -> enabled)
    const checkbox2 = checkboxes[1];
    expect(checkbox2).toBeDefined();
    if (checkbox2) {
      fireEvent.click(checkbox2);
      expect(mockUpdateJob).toHaveBeenCalledWith("test_job_2", {
        enabled: true,
      });
    }
  });

  it("renders global config input", () => {
    render(<ScheduledTasksConfig />);

    const durationInput = screen.getByLabelText("Max duration (hrs):");
    expect(durationInput).toBeInTheDocument();
    expect(durationInput).toHaveValue(10);

    fireEvent.change(durationInput, { target: { value: "12" } });
    expect(mockUpdateField).toHaveBeenCalledWith("duration_hours", 12);
  });
});
