import type { Metadata } from "next";
import "primeicons/primeicons.css";
import "../styles/globals.scss";

export const metadata: Metadata = {
  title: "Fundamental - Ebook Library",
  description: "Self-hosted ebook management and reading application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
