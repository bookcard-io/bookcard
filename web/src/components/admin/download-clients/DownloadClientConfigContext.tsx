import { createContext, type ReactNode, useContext } from "react";
import type { DownloadClientType } from "@/types/downloadClient";
import {
  CLIENT_CONFIGS,
  type ClientConfig,
  type ClientField,
  FIELD_DEFINITIONS,
} from "./clientConfig";

export interface DownloadClientConfig {
  configs: Record<DownloadClientType, ClientConfig>;
  fieldDefinitions: Record<
    ClientField,
    { label: string; type: string; placeholder?: string }
  >;
}

const DownloadClientConfigContext = createContext<DownloadClientConfig | null>(
  null,
);

export const defaultConfig: DownloadClientConfig = {
  configs: CLIENT_CONFIGS,
  fieldDefinitions: FIELD_DEFINITIONS,
};

interface DownloadClientConfigProviderProps {
  children: ReactNode;
  config?: DownloadClientConfig;
}

export function DownloadClientConfigProvider({
  children,
  config = defaultConfig,
}: DownloadClientConfigProviderProps) {
  return (
    <DownloadClientConfigContext.Provider value={config}>
      {children}
    </DownloadClientConfigContext.Provider>
  );
}

export function useDownloadClientConfig() {
  const context = useContext(DownloadClientConfigContext);
  if (!context) {
    throw new Error(
      "useDownloadClientConfig must be used within a DownloadClientConfigProvider",
    );
  }
  return context;
}
