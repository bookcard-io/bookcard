/**
 * Top 100 most popular languages by ISO 639-1 code.
 *
 * This list is ordered by approximate global usage and includes
 * the most commonly used languages for book metadata.
 *
 * Format: [ISO 639-1 code, Language name]
 */
export const POPULAR_LANGUAGES: Array<[string, string]> = [
  ["en", "English"],
  ["zh", "Chinese"],
  ["es", "Spanish"],
  ["hi", "Hindi"],
  ["ar", "Arabic"],
  ["pt", "Portuguese"],
  ["bn", "Bengali"],
  ["ru", "Russian"],
  ["ja", "Japanese"],
  ["pa", "Punjabi"],
  ["de", "German"],
  ["fr", "French"],
  ["ur", "Urdu"],
  ["id", "Indonesian"],
  ["it", "Italian"],
  ["tr", "Turkish"],
  ["vi", "Vietnamese"],
  ["ko", "Korean"],
  ["th", "Thai"],
  ["pl", "Polish"],
  ["uk", "Ukrainian"],
  ["ro", "Romanian"],
  ["nl", "Dutch"],
  ["el", "Greek"],
  ["cs", "Czech"],
  ["sv", "Swedish"],
  ["hu", "Hungarian"],
  ["fi", "Finnish"],
  ["da", "Danish"],
  ["no", "Norwegian"],
  ["he", "Hebrew"],
  ["sk", "Slovak"],
  ["bg", "Bulgarian"],
  ["hr", "Croatian"],
  ["sr", "Serbian"],
  ["sl", "Slovenian"],
  ["et", "Estonian"],
  ["lv", "Latvian"],
  ["lt", "Lithuanian"],
  ["mk", "Macedonian"],
  ["sq", "Albanian"],
  ["is", "Icelandic"],
  ["ga", "Irish"],
  ["mt", "Maltese"],
  ["cy", "Welsh"],
  ["eu", "Basque"],
  ["ca", "Catalan"],
  ["gl", "Galician"],
  ["fa", "Persian"],
  ["sw", "Swahili"],
  ["af", "Afrikaans"],
  ["zu", "Zulu"],
  ["xh", "Xhosa"],
  ["am", "Amharic"],
  ["ha", "Hausa"],
  ["yo", "Yoruba"],
  ["ig", "Igbo"],
  ["ta", "Tamil"],
  ["te", "Telugu"],
  ["ml", "Malayalam"],
  ["kn", "Kannada"],
  ["gu", "Gujarati"],
  ["mr", "Marathi"],
  ["ne", "Nepali"],
  ["si", "Sinhala"],
  ["my", "Myanmar"],
  ["km", "Khmer"],
  ["lo", "Lao"],
  ["ka", "Georgian"],
  ["hy", "Armenian"],
  ["az", "Azerbaijani"],
  ["kk", "Kazakh"],
  ["ky", "Kyrgyz"],
  ["uz", "Uzbek"],
  ["mn", "Mongolian"],
  ["be", "Belarusian"],
  ["bs", "Bosnian"],
  ["me", "Montenegrin"],
  ["lb", "Luxembourgish"],
  ["gd", "Scottish Gaelic"],
  ["br", "Breton"],
  ["co", "Corsican"],
  ["sc", "Sardinian"],
  ["oc", "Occitan"],
  ["rm", "Romansh"],
  ["wa", "Walloon"],
  ["fy", "Western Frisian"],
  ["yi", "Yiddish"],
  ["jv", "Javanese"],
  ["su", "Sundanese"],
  ["ms", "Malay"],
  ["tl", "Tagalog"],
  ["haw", "Hawaiian"],
  ["mi", "Maori"],
  ["sm", "Samoan"],
  ["to", "Tongan"],
  ["fj", "Fijian"],
  ["ty", "Tahitian"],
  ["mg", "Malagasy"],
  ["rw", "Kinyarwanda"],
  ["ny", "Chichewa"],
  ["sn", "Shona"],
  ["st", "Southern Sotho"],
  ["tn", "Tswana"],
  ["ve", "Venda"],
  ["ts", "Tsonga"],
  ["ss", "Swati"],
  ["nr", "Southern Ndebele"],
  ["nso", "Northern Sotho"],
  ["so", "Somali"],
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
  const entry = POPULAR_LANGUAGES.find(([langCode]) => langCode === code);
  return entry?.[1];
}

/**
 * Get all language codes.
 *
 * Returns
 * -------
 * string[]
 *     Array of ISO 639-1 language codes.
 */
export function getAllLanguageCodes(): string[] {
  return POPULAR_LANGUAGES.map(([code]) => code);
}
