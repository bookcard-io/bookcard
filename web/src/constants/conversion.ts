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

export const COMMON_TARGET_FORMATS = [
  "EPUB",
  "MOBI",
  "AZW3",
  "KEPUB",
  "PDF",
] as const;

export const STATUS_BADGE_CLASS_BY_STATUS: Record<string, string> = {
  completed: "bg-green-500/20 text-green-500",
  failed: "bg-red-500/20 text-red-500",
  error: "bg-red-500/20 text-red-500",
  pending: "bg-yellow-500/20 text-yellow-500",
  queued: "bg-yellow-500/20 text-yellow-500",
  running: "bg-yellow-500/20 text-yellow-500",
};
