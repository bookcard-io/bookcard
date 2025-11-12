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

export function BurgerArrowLeft(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      {...props}
      aria-label="Burger Arrow Left"
      role="img"
    >
      <path
        fill="currentColor"
        d="M7 6a1 1 0 0 1 1-1h12a1 1 0 1 1 0 2H8a1 1 0 0 1-1-1m-1.97 7.97L3.86 12.8H19a.8.8 0 0 0 0-1.6H3.86l1.17-1.17a.75.75 0 1 0-1.06-1.06l-2.5 2.5a.75.75 0 0 0 0 1.06l2.5 2.5a.75.75 0 0 0 1.06-1.06M8 17a1 1 0 1 0 0 2h12a1 1 0 1 0 0-2z"
      ></path>
    </svg>
  );
}
