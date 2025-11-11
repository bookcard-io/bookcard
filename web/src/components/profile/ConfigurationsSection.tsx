"use client";

import { DisplayModeConfiguration } from "./config/DisplayModeConfiguration";
import { LanguagesConfiguration } from "./config/LanguagesConfiguration";
import { MetadataProvidersConfiguration } from "./config/MetadataProvidersConfiguration";

/**
 * Configurations section for user preferences.
 *
 * Orchestrates display of all configuration options.
 * Follows SRP by delegating to specialized configuration components.
 * Follows SOC by separating each configuration concern.
 */
export function ConfigurationsSection() {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="m-0 font-semibold text-text-a0 text-xl">Configurations</h2>

      <div className="flex flex-col gap-6">
        <LanguagesConfiguration />
        <DisplayModeConfiguration />
        <MetadataProvidersConfiguration />
      </div>
    </div>
  );
}
