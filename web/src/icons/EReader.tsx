import type { SVGProps } from "react";

export function Ereader(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      {...props}
      aria-label="E-reader"
      role="img"
    >
      <path
        fill="currentColor"
        d="M7 3h9a3 3 0 0 1 3 3v13a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3Zm0 1a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H7Zm0 1h9a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm0 1v12h9V6H7Zm2 2h5v1H9V8Zm0 3h5v1H9v-1Zm0 3h3v1H9v-1Z"
      ></path>
    </svg>
  );
}
