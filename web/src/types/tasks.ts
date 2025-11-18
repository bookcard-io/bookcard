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

/**Task management types for frontend.

Type definitions matching the backend API schemas.
*/

export enum TaskStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export enum TaskType {
  BOOK_UPLOAD = "book_upload",
  MULTI_BOOK_UPLOAD = "multi_book_upload",
  BOOK_CONVERT = "book_convert",
  EMAIL_SEND = "email_send",
  METADATA_BACKUP = "metadata_backup",
  THUMBNAIL_GENERATE = "thumbnail_generate",
  LIBRARY_SCAN = "library_scan",
}

export interface Task {
  id: number;
  task_type: TaskType;
  status: TaskStatus;
  progress: number;
  user_id: number;
  username: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  error_message: string | null;
  metadata: Record<string, unknown> | null;
  duration: number | null;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskCancelResponse {
  success: boolean;
  message: string;
}

export interface TaskStatistics {
  task_type: TaskType;
  avg_duration: number | null;
  min_duration: number | null;
  max_duration: number | null;
  total_count: number;
  success_count: number;
  failure_count: number;
  last_run_at: string | null;
  success_rate: number;
}

export interface TaskTypesResponse {
  task_types: TaskType[];
}
