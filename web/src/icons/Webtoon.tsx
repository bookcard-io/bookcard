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

export function Webtoon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width="1em"
      height="1em"
      {...props}
      aria-label="Webtoon"
      role="img"
    >
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m11.361 38.149l13.418-1.658v5.21l15.708-7.282L42.5 21.336h-4.795l1.184-15.037l-30.311 4.677l2.605 9.768H5.5zm.159-13.082h4.924M13.982 32.5v-7.433"
      ></path>
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M31.556 32.5v-7.433L36.48 32.5v-7.433m-18.876 4.971a2.462 2.462 0 0 0 4.924 0V27.53a2.462 2.462 0 1 0-4.924 0Zm6.976 0a2.462 2.462 0 0 0 4.924 0V27.53a2.462 2.462 0 1 0-4.924 0Zm-1.159-7.105h3.716M23.421 15.5h3.716m-3.716 3.716h2.423M23.421 15.5v7.433M21.446 15.5l-1.858 7.433l-1.859-7.433l-1.858 7.433l-1.858-7.433m18.116 3.716a1.858 1.858 0 0 1 0 3.717h-3.066V15.5h3.066a1.858 1.858 0 0 1 0 3.716m0 0h-3.066"
      ></path>
    </svg>
  );
}
