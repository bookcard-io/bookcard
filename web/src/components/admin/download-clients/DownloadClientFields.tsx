import { NumberInput } from "@/components/forms/NumberInput";
import { TextInput } from "@/components/forms/TextInput";
import type { ClientField } from "./clientConfig";
import { useDownloadClientConfig } from "./DownloadClientConfigContext";
import type { DownloadClientFormData } from "./useDownloadClientForm";

interface DynamicFieldProps {
  field: ClientField;
  value: string | number | boolean;
  onChange: (value: string | number | boolean) => void;
  isEditMode: boolean;
  required?: boolean;
}

export function DynamicField({
  field,
  value,
  onChange,
  isEditMode,
  required,
}: DynamicFieldProps) {
  const { fieldDefinitions } = useDownloadClientConfig();
  const definition = fieldDefinitions[field];

  if (!definition) return null;

  if (definition.type === "checkbox") {
    return (
      <div className="flex items-center gap-2 md:col-span-2">
        <input
          type="checkbox"
          id={field}
          checked={!!value}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-[var(--color-primary-a0)] focus:ring-[var(--color-primary-a0)]"
        />
        <label htmlFor={field} className="text-sm text-text-a0">
          {definition.label}
        </label>
      </div>
    );
  }

  if (definition.type === "number") {
    return (
      <NumberInput
        id={field}
        label={definition.label}
        value={value as number}
        onChange={(e) => onChange(Number.parseInt(e.target.value, 10) || 0)}
        placeholder={definition.placeholder}
      />
    );
  }

  return (
    <TextInput
      id={field}
      label={definition.label}
      value={(value as string) || ""}
      onChange={(e) => onChange(e.target.value)}
      type={definition.type}
      placeholder={
        definition.type === "password" && isEditMode
          ? "Leave blank to keep unchanged"
          : definition.placeholder
      }
      required={required}
      autoComplete={
        field === "username"
          ? "username"
          : field === "password"
            ? "current-password"
            : undefined
      }
    />
  );
}

interface FieldGroupProps {
  fields: ClientField[];
  formData: DownloadClientFormData;
  onChange: (field: ClientField, value: string | number | boolean) => void;
  isEditMode: boolean;
  requiredFields?: ClientField[];
}

export function FieldGroup({
  fields,
  formData,
  onChange,
  isEditMode,
  requiredFields = [],
}: FieldGroupProps) {
  if (fields.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      {fields.map((field) => (
        <DynamicField
          key={field}
          field={field}
          value={
            formData[field as keyof DownloadClientFormData] as
              | string
              | number
              | boolean
          }
          onChange={(value) => onChange(field, value)}
          isEditMode={isEditMode}
          required={requiredFields.includes(field)}
        />
      ))}
    </div>
  );
}
