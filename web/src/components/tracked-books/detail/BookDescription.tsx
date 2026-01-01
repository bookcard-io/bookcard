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

"use client";

import { useState } from "react";

const MAX_CHARS = 400;

export function BookDescription({ description }: { description?: string }) {
  const [expanded, setExpanded] = useState(false);

  if (!description) return null;

  if (description.length <= MAX_CHARS) {
    return (
      <p className="max-w-4xl text-text-a20 leading-relaxed">{description}</p>
    );
  }

  return (
    <div className="max-w-4xl text-text-a20 leading-relaxed">
      {expanded ? (
        <>
          {description}
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="ml-2 cursor-pointer font-bold text-primary-a0 hover:text-primary-a10"
          >
            Less
          </button>
        </>
      ) : (
        <>
          {description.substring(0, MAX_CHARS)}...
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="ml-2 cursor-pointer font-bold text-primary-a0 hover:text-primary-a10"
          >
            More
          </button>
        </>
      )}
    </div>
  );
}
