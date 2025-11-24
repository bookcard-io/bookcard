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

export function ReadingMode(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 2048 2048"
      width="1em"
      height="1em"
      {...props}
      aria-label="Reading Mode"
      role="img"
    >
      <path
        fill="currentColor"
        d="M1920 256v1664H0V256h256V128h384q88 0 169 27t151 81q69-54 150-81t170-27h384v128zm-640 0q-70 0-136 23t-120 69v1254q59-33 124-49t132-17h256V256zM384 1536h256q67 0 132 16t124 50V348q-54-45-120-68t-136-24H384zm-256 256h806q-32-31-65-54t-68-40t-75-25t-86-9H256V384H128zM1792 384h-128v1280h-384q-46 0-85 8t-75 25t-69 40t-65 55h806z"
      ></path>
    </svg>
  );
}
