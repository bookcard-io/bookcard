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

export function LibraryOutline(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      width="1em"
      height="1em"
      {...props}
      aria-label="Library Outline"
      role="img"
    >
      <rect
        width="64"
        height="368"
        x="32"
        y="96"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        rx="16"
        ry="16"
      ></rect>
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="32"
        d="M112 224h128M112 400h128"
      ></path>
      <rect
        width="128"
        height="304"
        x="112"
        y="160"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        rx="16"
        ry="16"
      ></rect>
      <rect
        width="96"
        height="416"
        x="256"
        y="48"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        rx="16"
        ry="16"
      ></rect>
      <path
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        d="m422.46 96.11l-40.4 4.25c-11.12 1.17-19.18 11.57-17.93 23.1l34.92 321.59c1.26 11.53 11.37 20 22.49 18.84l40.4-4.25c11.12-1.17 19.18-11.57 17.93-23.1L445 115c-1.31-11.58-11.42-20.06-22.54-18.89Z"
      ></path>
    </svg>
  );
}
