import { useRef } from "react";
import { FaSpinner, FaUpload } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { validatePluginZipFile } from "@/utils/plugins/validation";

export interface PluginUploadFormProps {
  installing: boolean;
  installFromUpload: (file: File) => Promise<boolean>;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showDanger: (message: string) => void;
}

export function PluginUploadForm({
  installing,
  installFromUpload,
  showSuccess,
  showWarning,
  showDanger,
}: PluginUploadFormProps): React.ReactElement {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validationError = validatePluginZipFile(file);
    if (validationError) {
      showWarning(validationError);
      return;
    }

    try {
      const ok = await installFromUpload(file);
      if (ok) {
        showSuccess("Plugin installed successfully!");
      }
    } catch (error) {
      console.error("Failed to install plugin", error);
      showDanger(
        `Failed to install plugin: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-medium text-[var(--color-text-a10)]">Upload ZIP</h3>
      <p className="text-[var(--color-text-a30)] text-sm">
        Upload a plugin ZIP file directly from your computer.
      </p>
      <div className="flex items-center gap-2">
        <input
          type="file"
          ref={fileInputRef}
          accept=".zip"
          className="hidden"
          onChange={handleFileUpload}
        />
        <Button
          variant="primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={installing}
        >
          {installing ? (
            <>
              <FaSpinner className="animate-spin" />
              Installing...
            </>
          ) : (
            <>
              <FaUpload />
              Select File
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
