import type { SVGProps } from "react";

export function GridView(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      width="1em"
      height="1em"
      {...props}
      aria-label="Grid View"
      role="img"
    >
      <rect
        width="160"
        height="160"
        x="48"
        y="48"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        rx="16"
        ry="16"
      />
      <rect
        width="160"
        height="160"
        x="304"
        y="48"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        rx="16"
        ry="16"
      />
      <rect
        width="160"
        height="160"
        x="48"
        y="304"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        rx="16"
        ry="16"
      />
      <rect
        width="160"
        height="160"
        x="304"
        y="304"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="32"
        rx="16"
        ry="16"
      />
    </svg>
  );
}
