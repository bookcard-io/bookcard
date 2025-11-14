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

export function Kindle(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width="1em"
      height="1em"
      {...props}
      aria-label="Kindle"
      role="img"
    >
      <path
        fill="#37474F"
        d="M8 41V7c0-2.2 1.8-4 4-4h24c2.2 0 4 1.8 4 4v34c0 2.2-1.8 4-4 4H12c-2.2 0-4-1.8-4-4"
      ></path>
      <path
        fill="#eee"
        d="M35 6H13c-.6 0-1 .4-1 1v29c0 .6.4 1 1 1h22c.6 0 1-.4 1-1V7c0-.6-.4-1-1-1"
      ></path>
      <path fill="#546E7A" d="M20 40h8v2h-8z"></path>
      <path
        fill="#A1A1A1"
        d="M16 11h16v3H16zm0 7h16v2H16zm0 4h12v2H16zm0 4h16v2H16zm0 4h12v2H16z"
      ></path>
    </svg>
  );
}
