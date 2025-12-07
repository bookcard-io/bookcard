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

export function PageScroll(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width="1em"
      height="1em"
      {...props}
      aria-label="Page Scroll"
      role="img"
    >
      <path
        d="M16 28H4a1.89 1.89 0 0 1-2-2V14a1.89 1.89 0 0 1 2-2h12a1.89 1.89 0 0 1 2 2v12a1.89 1.89 0 0 1-2 2zM4 14v12h12V14z"
        fill="currentColor"
      ></path>
      <path
        d="M22 19h-2v-9H10V8h10a1.89 1.89 0 0 1 2 2z"
        fill="currentColor"
      ></path>
      <path
        d="M26 14h-2V6h-8V4h8a1.89 1.89 0 0 1 2 2z"
        fill="currentColor"
      ></path>
      <path
        d="M24 17v2h2.8L22 24.4V22h-2v6h6v-2h-2.8l4.8-5.4V23h2v-6h-6z"
        fill="currentColor"
      ></path>
    </svg>
  );
}
