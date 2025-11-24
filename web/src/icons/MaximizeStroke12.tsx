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

export function MaximizeStroke12(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 12 12"
      width="1em"
      height="1em"
      {...props}
      aria-label="Maximize Stroke 12"
      role="img"
    >
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        d="M.5 3.5V1C.5.7.7.5 1 .5h2.5m8 3V1c0-.3-.2-.5-.5-.5H8.5m3 8V11c0 .3-.2.5-.5.5H8.5m-8-3V11c0 .3.2.5.5.5h2.5m0-8L1 1m7.5 7.5L11 11M8.5 3.5L11 1M3.5 8.5L1 11"
      ></path>
    </svg>
  );
}
