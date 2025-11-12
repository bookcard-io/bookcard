import type { SVGProps } from "react";

export function BurgerArrowRight(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      {...props}
      aria-label="Burger Arrow Right"
      role="img"
    >
      <path
        fill="currentColor"
        d="M3 6a1 1 0 0 1 1-1h12a1 1 0 1 1 0 2H4a1 1 0 0 1-1-1m1.25 6a.75.75 0 0 1 .75-.75h15.19l-1.22-1.22a.75.75 0 1 1 1.06-1.06l2.5 2.5a.75.75 0 0 1 0 1.06l-2.5 2.5a.75.75 0 1 1-1.06-1.06l1.22-1.22H5a.75.75 0 0 1-.75-.75M4 17a1 1 0 1 0 0 2h12a1 1 0 1 0 0-2z"
      ></path>
    </svg>
  );
}
