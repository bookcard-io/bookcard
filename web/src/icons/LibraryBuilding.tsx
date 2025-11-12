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

export function LibraryBuilding(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      width="1em"
      height="1em"
      {...props}
      aria-label="Library Building"
      role="img"
    >
      <path
        fill="currentColor"
        d="M247.759 14.358L16 125.946V184h480v-58.362ZM464 152H48v-5.946l200.241-96.412L464 146.362ZM16 496h480V392H16Zm32-72h416v40H48Zm24-216h32v160H72zm336 0h32v160h-32zm-224 0h32v160h-32zm112 0h32v160h-32z"
      ></path>
    </svg>
  );
}
