import { useCallback, useState } from "react";
import type {
  DownloadClient,
  DownloadClientCreate,
  DownloadClientTestResponse,
} from "@/types/downloadClient";

interface UseConnectionTestProps {
  testConnection: (id: number) => Promise<DownloadClientTestResponse>;
  testNewConnection: (
    data: DownloadClientCreate,
  ) => Promise<DownloadClientTestResponse>;
  initialData?: DownloadClient;
  getPayload: () => DownloadClientCreate;
}

export function useConnectionTest({
  testConnection,
  testNewConnection,
  initialData,
  getPayload,
}: UseConnectionTestProps) {
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] =
    useState<DownloadClientTestResponse | null>(null);

  const handleTest = useCallback(async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      let result: DownloadClientTestResponse;
      if (initialData) {
        result = await testConnection(initialData.id);
      } else {
        const payload = getPayload();
        result = await testNewConnection(payload);
      }
      setTestResult(result);
    } catch (_e) {
      setTestResult({
        success: false,
        message: "Connection failed",
      });
    } finally {
      setIsTesting(false);
    }
  }, [initialData, testConnection, testNewConnection, getPayload]);

  return { isTesting, testResult, handleTest };
}
