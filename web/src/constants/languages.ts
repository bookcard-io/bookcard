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

/**
 * Language entry type.
 */
export type LanguageEntry = {
  code: string;
  name: string;
  flag: string;
  englishName: string;
};

/**
 * Top 100 most popular languages by ISO 639-1 code.
 *
 * This list is ordered by approximate global usage and includes
 * the most commonly used languages for book metadata.
 *
 * Format: Object with code, name, flag, and englishName properties.
 */
export const POPULAR_LANGUAGES: Array<LanguageEntry> = [
  { code: "af", name: "Afrikaans", flag: "🇿🇦", englishName: "Afrikaans" },
  { code: "sq", name: "Shqip", flag: "🇦🇱", englishName: "Albanian" },
  { code: "am", name: "አማርኛ", flag: "🇪🇹", englishName: "Amharic" },
  {
    code: "en-AU",
    name: "English (Australia)",
    flag: "🇦🇺",
    englishName: "English",
  },
  {
    code: "en-CA",
    name: "English (Canada)",
    flag: "🇨🇦",
    englishName: "English",
  },
  {
    code: "en-GB",
    name: "English (United Kingdom)",
    flag: "🇬🇧",
    englishName: "English",
  },
  { code: "en", name: "English", flag: "🇺🇸", englishName: "English" },
  { code: "ar", name: "العربية", flag: "🇸🇦", englishName: "Arabic" },
  { code: "hy", name: "Հայերեն", flag: "🇦🇲", englishName: "Armenian" },
  { code: "my", name: "ဗမာ", flag: "🇲🇲", englishName: "Burmese" },
  { code: "eu", name: "Euskara", flag: "🇪🇸", englishName: "Basque" },
  { code: "bn", name: "বাংলা", flag: "🇧🇩", englishName: "Bengali" },
  { code: "bg", name: "Български", flag: "🇧🇬", englishName: "Bulgarian" },
  { code: "be", name: "Беларуская", flag: "🇧🇾", englishName: "Belarusian" },
  { code: "hr", name: "Hrvatski", flag: "🇭🇷", englishName: "Croatian" },
  { code: "da", name: "Dansk", flag: "🇩🇰", englishName: "Danish" },
  { code: "et", name: "Eesti", flag: "🇪🇪", englishName: "Estonian" },
  { code: "tl", name: "Filipino", flag: "🇵🇭", englishName: "Filipino" },
  { code: "fi", name: "Suomi", flag: "🇫🇮", englishName: "Finnish" },
  {
    code: "fr-FR",
    name: "Français (France)",
    flag: "🇫🇷",
    englishName: "French",
  },
  {
    code: "fr-CA",
    name: "Français (Canada)",
    flag: "🇨🇦",
    englishName: "French",
  },
  { code: "gl", name: "Galego", flag: "🇪🇸", englishName: "Galician" },
  { code: "ka", name: "ქართული", flag: "🇬🇪", englishName: "Georgian" },
  { code: "gu", name: "ગુજરાતી", flag: "🇮🇳", englishName: "Gujarati" },
  { code: "he", name: "עברית", flag: "🇮🇱", englishName: "Hebrew" },
  { code: "hi", name: "हिन्दी", flag: "🇮🇳", englishName: "Hindi" },
  { code: "id", name: "Indonesia", flag: "🇮🇩", englishName: "Indonesian" },
  { code: "is", name: "Íslenska", flag: "🇮🇸", englishName: "Icelandic" },
  { code: "it", name: "Italiano", flag: "🇮🇹", englishName: "Italian" },
  { code: "ja", name: "日本語", flag: "🇯🇵", englishName: "Japanese" },
  { code: "kn", name: "ಕನ್ನಡ", flag: "🇮🇳", englishName: "Kannada" },
  { code: "ca", name: "Català", flag: "🇪🇸", englishName: "Catalan" },
  { code: "kk", name: "Қазақ тілі", flag: "🇰🇿", englishName: "Kazakh" },
  { code: "km", name: "ខ្មែរ", flag: "🇰🇭", englishName: "Khmer" },
  { code: "ko", name: "한국어", flag: "🇰🇷", englishName: "Korean" },
  { code: "ky", name: "Кыргызча", flag: "🇰🇬", englishName: "Kyrgyz" },
  { code: "lo", name: "ລາວ", flag: "🇱🇦", englishName: "Lao" },
  { code: "lt", name: "Lietuvių", flag: "🇱🇹", englishName: "Lithuanian" },
  { code: "lv", name: "Latviešu", flag: "🇱🇻", englishName: "Latvian" },
  { code: "mk", name: "Македонски", flag: "🇲🇰", englishName: "Macedonian" },
  { code: "ml", name: "മലയാളം", flag: "🇮🇳", englishName: "Malayalam" },
  {
    code: "ms-MY",
    name: "Bahasa Melayu (Malaysia)",
    flag: "🇲🇾",
    englishName: "Malay (Malaysia)",
  },
  { code: "ms", name: "Bahasa Melayu", flag: "🇲🇾", englishName: "Malay" },
  { code: "mr", name: "मराठी", flag: "🇮🇳", englishName: "Marathi" },
  { code: "hu", name: "Magyar", flag: "🇭🇺", englishName: "Hungarian" },
  { code: "mn", name: "Монгол", flag: "🇲🇳", englishName: "Mongolian" },
  { code: "ne", name: "नेपाली", flag: "🇳🇵", englishName: "Nepali" },
  { code: "nl", name: "Nederlands", flag: "🇳🇱", englishName: "Dutch" },
  { code: "no", name: "Norsk", flag: "🇳🇴", englishName: "Norwegian" },
  { code: "de", name: "Deutsch", flag: "🇩🇪", englishName: "German" },
  { code: "pa", name: "ਪੰਜਾਬੀ", flag: "🇮🇳", englishName: "Punjabi" },
  { code: "fa", name: "فارسی", flag: "🇮🇷", englishName: "Persian" },
  { code: "pl", name: "Polski", flag: "🇵🇱", englishName: "Polish" },
  {
    code: "pt-BR",
    name: "Português (Brasil)",
    flag: "🇧🇷",
    englishName: "Portuguese (Brazil)",
  },
  {
    code: "pt-PT",
    name: "Português (Portugal)",
    flag: "🇵🇹",
    englishName: "Portuguese (Portugal)",
  },
  { code: "ro", name: "Română", flag: "🇷🇴", englishName: "Romanian" },
  { code: "ru", name: "Русский", flag: "🇷🇺", englishName: "Russian" },
  { code: "rm", name: "Rumantsch", flag: "🇨🇭", englishName: "Romansh" },
  { code: "si", name: "සිංහල", flag: "🇱🇰", englishName: "Sinhala" },
  { code: "sk", name: "Slovenčina", flag: "🇸🇰", englishName: "Slovak" },
  { code: "sl", name: "Slovenščina", flag: "🇸🇮", englishName: "Slovenian" },
  { code: "sr", name: "Српски", flag: "🇷🇸", englishName: "Serbian" },
  { code: "sw", name: "Kiswahili", flag: "🇹🇿", englishName: "Swahili" },
  { code: "ta", name: "தமிழ்", flag: "🇮🇳", englishName: "Tamil" },
  { code: "te", name: "తెలుగు", flag: "🇮🇳", englishName: "Telugu" },
  { code: "th", name: "ไทย", flag: "🇹🇭", englishName: "Thai" },
  { code: "tr", name: "Türkçe", flag: "🇹🇷", englishName: "Turkish" },
  { code: "uk", name: "Українська", flag: "🇺🇦", englishName: "Ukrainian" },
  { code: "ur", name: "اردو", flag: "🇵🇰", englishName: "Urdu" },
  { code: "vi", name: "Tiếng Việt", flag: "🇻🇳", englishName: "Vietnamese" },
  { code: "zu", name: "Zulu", flag: "🇿🇦", englishName: "Zulu" },
  {
    code: "az",
    name: "Azərbaycan dili",
    flag: "🇦🇿",
    englishName: "Azerbaijani",
  },
  { code: "cs", name: "Čeština", flag: "🇨🇿", englishName: "Czech" },
  {
    code: "zh-HK",
    name: "中文（香港）",
    englishName: "Chinese (Hong Kong)",
    flag: "🇭🇰",
  },
  {
    code: "zh-TW",
    name: "中文（繁體）",
    englishName: "Chinese (Traditional)",
    flag: "🇹🇼",
  },
  {
    code: "zh",
    name: "中文（简体）",
    englishName: "Chinese (Simplified)",
    flag: "🇨🇳",
  },
  { code: "el", name: "Ελληνικά", englishName: "Greek", flag: "🇬🇷" },
  {
    code: "es-419",
    name: "Español (Latinoamérica)",
    englishName: "Spanish (Latin America)",
    flag: "🌎",
  },
  {
    code: "es-US",
    name: "Español (Estados Unidos)",
    englishName: "Spanish (United States)",
    flag: "🇺🇸",
  },
  {
    code: "es",
    name: "Español (España)",
    englishName: "Spanish (Spain)",
    flag: "🇪🇸",
  },
  { code: "sv", name: "Svenska", englishName: "Swedish", flag: "🇸🇪" },
];

/**
 * Get language code by ISO 639-1 code.
 *
 * Parameters
 * ----------
 * code : string
 *     ISO 639-1 language code.
 *
 * Returns
 * -------
 * string | undefined
 *     Language name if found, undefined otherwise.
 */
export function getLanguageName(code: string): string | undefined {
  // Extract ISO-639-1 base code (part before the dash)
  const baseCode = code.split("-")[0] as string;
  // Find first instance with matching base code
  const entry = POPULAR_LANGUAGES.find(
    (lang) => lang.code.split("-")[0] === baseCode,
  );
  return entry?.name;
}

/**
 * Get all language codes.
 *
 * Returns
 * -------
 * string[]
 *     Array of unique ISO 639-1 language codes (without dashes).
 */
export function getAllLanguageCodes(): string[] {
  const codes = POPULAR_LANGUAGES.map((lang) => {
    // Extract ISO-639-1 code (part before the dash)
    return lang.code.split("-")[0] as string;
  });
  // De-duplicate using Set
  return Array.from(new Set(codes));
}
