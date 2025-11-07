import type { SVGProps } from "react";

export function ListView(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      width="1em"
      height="1em"
      {...props}
      aria-label="List View"
      role="img"
    >
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="32"
        d="M160 144h288M160 256h288M160 368h288"
      />
      <circle cx="80" cy="144" r="16" fill="currentColor" />
      <circle cx="80" cy="256" r="16" fill="currentColor" />
      <circle cx="80" cy="368" r="16" fill="currentColor" />
    </svg>
  );
}
