import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import type { Book } from "@/types/book";
import { getPreferredReadableFormat } from "@/utils/bookFormats";

export function useBookNavigation(book: Book) {
  const router = useRouter();
  const [isNavigating, setIsNavigating] = useState(false);

  const readableFormat = useMemo(
    () => getPreferredReadableFormat(book.formats || []),
    [book.formats],
  );

  const navigateToReader = useCallback(() => {
    if (!readableFormat) return;
    setIsNavigating(true);
    router.push(`/reading/${book.id}/${readableFormat}`);
  }, [book.id, readableFormat, router]);

  return { isNavigating, readableFormat, navigateToReader };
}
