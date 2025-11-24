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

import type { SVGProps } from "react";

export function Notebook(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width="1em"
      height="1em"
      {...props}
      aria-label="Notebook"
      role="img"
    >
      <g
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="4"
      >
        <path d="M10 6a2 2 0 0 1 2-2h28a2 2 0 0 1 2 2v36a2 2 0 0 1-2 2H12a2 2 0 0 1-2-2z"></path>
        <path
          strokeLinecap="round"
          d="M34 6v36M6 14h8M6 24h8M6 34h8M27 4h12M27 44h12"
        ></path>
      </g>
    </svg>
  );
}
