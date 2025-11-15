import type { SVGProps } from "react";

export function Nook(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width="1em"
      height="1em"
      {...props}
      aria-label="Nook"
      role="img"
    >
      <path
        fill="#90A4AE"
        d="M8 39V9c0-3.3 2.7-6 6-6h20c3.3 0 6 2.7 6 6v30c0 3.3-2.7 6-6 6H14c-3.3 0-6-2.7-6-6"
      ></path>
      <path
        fill="#ECEFF1"
        d="M34 7H14c-1.1 0-2 .9-2 2v26c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2"
      ></path>
      <path
        fill="#B0BEC5"
        d="M16 12h16v3H16zm0 7h16v2H16zm0 4h12v2H16zm0 4h16v2H16zm0 4h12v2H16z"
      ></path>
      <path
        fill="none"
        stroke="#eee"
        strokeMiterlimit="10"
        strokeWidth="2"
        d="M22 43v-1c0-1.1.9-2 2-2s2 .9 2 2v1"
      ></path>
    </svg>
  );
}
