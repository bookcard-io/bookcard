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

import Link from "next/link";
import type { ReactNode } from "react";
import { Button, type ButtonProps } from "@/components/forms/Button";

interface PrimaryButtonProps extends Omit<ButtonProps, "variant"> {
  href?: string;
  children: ReactNode;
}

export function PrimaryButton({
  children,
  href,
  className,
  ...props
}: PrimaryButtonProps) {
  // We use the Button component for consistent styling
  // But we can't directly use Button if it renders a button element and we need a link
  // The existing Button component renders a <button>.
  // So we will replicate the styling or wrap it.
  // Since Button forwards ref and is a button, we can't easily turn it into a Link unless it supports 'as' prop.
  // Looking at Button source, it does NOT support 'as' or 'component'.
  // So we will use the same classes or wrap it.

  // Actually, checking Button.tsx again:
  // It uses specific classes. I should probably just use Link with those classes if href is present.

  const baseClasses =
    "flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 font-medium text-sm text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed";

  if (href) {
    return (
      <Link href={href} className={`${baseClasses} ${className || ""}`}>
        {children}
      </Link>
    );
  }

  return (
    <Button variant="primary" className={className} {...props}>
      {children}
    </Button>
  );
}
