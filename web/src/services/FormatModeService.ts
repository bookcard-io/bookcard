import { SUPPORTED_BOOK_FORMAT_EXTENSIONS } from "@/constants/bookFormats";
import { AUDIOBOOK_FORMATS, COMIC_FORMATS } from "@/utils/formatUtils";

export type FormatMode = "any" | "book" | "comic" | "audiobook" | "custom";

export interface FormatOption {
  id: FormatMode;
  label: string;
  formats: string[];
}

export class FormatModeService {
  private comicFormats: string[];
  private audiobookFormats: string[];
  private bookFormats: string[];

  constructor() {
    this.comicFormats = COMIC_FORMATS.map((f) => f.toLowerCase());
    this.audiobookFormats = AUDIOBOOK_FORMATS.map((f) => f.toLowerCase());
    this.bookFormats = SUPPORTED_BOOK_FORMAT_EXTENSIONS.filter(
      (f) =>
        !this.comicFormats.includes(f) && !this.audiobookFormats.includes(f),
    );
  }

  public detect(selectedFormats: string[]): FormatMode {
    if (selectedFormats.length === 0) return "any";
    if (this.matchesExactly(selectedFormats, this.comicFormats)) return "comic";
    if (this.matchesExactly(selectedFormats, this.audiobookFormats))
      return "audiobook";
    if (this.matchesExactly(selectedFormats, this.bookFormats)) return "book";
    return "custom";
  }

  public getOptions(): FormatOption[] {
    return [
      { id: "any", label: "Any", formats: [] },
      { id: "audiobook", label: "Audiobook", formats: this.audiobookFormats },
      { id: "book", label: "Book", formats: this.bookFormats },
      { id: "comic", label: "Comic", formats: this.comicFormats },
    ];
  }

  public getFormatsForMode(mode: FormatMode): string[] {
    const option = this.getOptions().find((opt) => opt.id === mode);
    return option?.formats || [];
  }

  private matchesExactly(selected: string[], target: string[]): boolean {
    return (
      selected.length === target.length &&
      selected.every((f) => target.includes(f))
    );
  }
}

export const formatModeService = new FormatModeService();
