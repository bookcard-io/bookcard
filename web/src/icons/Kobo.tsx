import type { SVGProps } from "react";

export function KoboBooks(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width="1em"
      height="1em"
      {...props}
      aria-label="Kobo Books"
      role="img"
    >
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M38.5 5.5h-29a4 4 0 0 0-4 4v29a4 4 0 0 0 4 4h29a4 4 0 0 0 4-4v-29a4 4 0 0 0-4-4"
      ></path>
      <rect
        width="5.435"
        height="7.202"
        x="33.065"
        y="20.341"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        rx="2.717"
        ry="2.717"
      ></rect>
      <rect
        width="5.435"
        height="7.202"
        x="16.922"
        y="20.341"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        rx="2.717"
        ry="2.717"
      ></rect>
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.5 16.673v10.87m.001-2.309l4.92-4.897m-3.354 3.338l3.868 3.851m10.015-4.467a2.72 2.72 0 0 1 2.718-2.718h0c1.5 0 2.717 1.217 2.717 2.718v1.766a2.717 2.717 0 0 1-2.717 2.718h0a2.717 2.717 0 0 1-2.718-2.718m0 2.718v-10.87"
      ></path>
    </svg>
  );
}
