import { useEffect, useState } from "react";
import type { BasicConfig } from "@/services/basicConfigService";
import { fetchPublicBasicConfig } from "@/services/basicConfigService";

export interface UseAnonymousAccessConfigResult {
  config: BasicConfig | null;
  isLoading: boolean;
  error: string | null;
}

export function useAnonymousAccessConfig(): UseAnonymousAccessConfigResult {
  const [config, setConfig] = useState<BasicConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchPublicBasicConfig();
        setConfig(data);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load configuration";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  return { config, isLoading, error };
}
