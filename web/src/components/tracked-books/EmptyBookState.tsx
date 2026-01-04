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

import { FaSearch } from "react-icons/fa";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { ROUTES } from "@/constants/routes";

export function EmptyBookState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center text-center">
      <div className="mb-4 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
        <FaSearch className="h-8 w-8 text-gray-400" />
      </div>
      <h3 className="mb-2 font-medium text-gray-900 text-lg dark:text-gray-100">
        No books tracked yet
      </h3>
      <p className="mb-6 max-w-sm text-gray-500 dark:text-gray-400">
        Search for books to add them to your watch list. We'll automatically
        download them when they become available.
      </p>
      <PrimaryButton href={ROUTES.TRACKED_BOOKS_ADD}>
        Add Your First Book
      </PrimaryButton>
    </div>
  );
}
