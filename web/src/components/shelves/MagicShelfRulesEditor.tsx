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

"use client";

import { useCallback } from "react";
import { FaFolderOpen, FaPlus, FaTimes, FaTrash } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { Select } from "@/components/forms/Select";
import { TextInput } from "@/components/forms/TextInput";
import { cn } from "@/libs/utils";
import {
  type FilterGroup,
  type FilterRule,
  isFilterGroup,
  JoinType,
  RuleField,
  RuleOperator,
  type RuleValue,
} from "@/types/magicShelf";

interface MagicShelfRulesEditorProps {
  rootGroup: FilterGroup;
  onChange: (group: FilterGroup) => void;
  disabled?: boolean;
}

export function MagicShelfRulesEditor({
  rootGroup,
  onChange,
  disabled,
}: MagicShelfRulesEditorProps) {
  const handleUpdate = useCallback(
    (newGroup: FilterGroup) => {
      onChange(newGroup);
    },
    [onChange],
  );

  return (
    <div className="flex flex-col gap-4">
      <RuleGroupEditor
        group={rootGroup}
        onChange={handleUpdate}
        onRemove={() => {}} // Root group cannot be removed
        isRoot={true}
        disabled={disabled}
      />
    </div>
  );
}

interface RuleGroupEditorProps {
  group: FilterGroup;
  onChange: (group: FilterGroup) => void;
  onRemove: () => void;
  isRoot?: boolean;
  disabled?: boolean;
  depth?: number;
}

const NESTING_COLORS = [
  "border-primary-a20", // Depth 0 (Root) - Primary
  "border-success-a20", // Depth 1
  "border-warning-a20", // Depth 2
  "border-info-a20", // Depth 3
  "border-danger-a20", // Depth 4
];

function getBorderColor(depth: number): string {
  return (
    NESTING_COLORS[depth % NESTING_COLORS.length] ??
    NESTING_COLORS[0] ??
    "border-primary-a20"
  );
}

function RuleGroupEditor({
  group,
  onChange,
  onRemove,
  isRoot = false,
  disabled,
  depth = 0,
}: RuleGroupEditorProps) {
  const handleJoinTypeChange = (value: string) => {
    onChange({ ...group, join_type: value as JoinType });
  };

  const handleAddRule = () => {
    const newRule: FilterRule = {
      field: RuleField.TITLE,
      operator: RuleOperator.CONTAINS,
      value: "",
    };
    onChange({ ...group, rules: [...group.rules, newRule] });
  };

  const handleAddGroup = () => {
    const newGroup: FilterGroup = {
      join_type: JoinType.AND,
      rules: [
        {
          field: RuleField.TITLE,
          operator: RuleOperator.CONTAINS,
          value: "",
        },
      ],
    };
    onChange({ ...group, rules: [...group.rules, newGroup] });
  };

  const handleRuleChange = (
    index: number,
    newRule: FilterRule | FilterGroup,
  ) => {
    const newRules = [...group.rules];
    newRules[index] = newRule;
    onChange({ ...group, rules: newRules });
  };

  const handleRemoveItem = (index: number) => {
    const newRules = group.rules.filter((_, i) => i !== index);
    onChange({ ...group, rules: newRules });
  };

  return (
    <div
      className={cn(
        "flex w-full flex-col gap-3 rounded-md border p-3",
        isRoot
          ? "border-surface-a20 bg-surface-a0"
          : "border-surface-a30 bg-surface-a10",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-text-a20">Match</span>
          <div className="w-24 min-w-[6rem]">
            <Select
              value={group.join_type}
              onChange={(e) => handleJoinTypeChange(e.target.value)}
              disabled={disabled}
            >
              <option value={JoinType.AND}>ALL</option>
              <option value={JoinType.OR}>ANY</option>
            </Select>
          </div>
          <span className="font-medium text-sm text-text-a20">
            of the following rules:
          </span>
        </div>
        {!isRoot && (
          <Button
            variant="ghost"
            size="small"
            onClick={onRemove}
            disabled={disabled}
            className="text-danger-a0 hover:text-danger-a10"
            aria-label="Remove group"
          >
            <FaTrash />
          </Button>
        )}
      </div>

      <div
        className={cn(
          "flex flex-col gap-2 border-l-2 pl-4",
          getBorderColor(depth),
        )}
      >
        {group.rules.map((rule, index) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: Rules don't have unique IDs and order matters
          <div key={index} className="flex flex-col">
            {isFilterGroup(rule) ? (
              <RuleGroupEditor
                group={rule}
                onChange={(updatedGroup) =>
                  handleRuleChange(index, updatedGroup)
                }
                onRemove={() => handleRemoveItem(index)}
                disabled={disabled}
                depth={depth + 1}
              />
            ) : (
              <RuleItemEditor
                rule={rule}
                onChange={(updatedRule) => handleRuleChange(index, updatedRule)}
                onRemove={() => handleRemoveItem(index)}
                disabled={disabled}
              />
            )}
          </div>
        ))}

        <div className="mt-2 flex gap-2">
          <Button
            variant="secondary"
            size="small"
            onClick={handleAddRule}
            disabled={disabled}
          >
            <FaPlus />
            Add Rule
          </Button>
          <Button
            variant="ghost"
            size="small"
            onClick={handleAddGroup}
            disabled={disabled}
          >
            <FaFolderOpen />
            Add Group
          </Button>
        </div>
      </div>
    </div>
  );
}

interface RuleItemEditorProps {
  rule: FilterRule;
  onChange: (rule: FilterRule) => void;
  onRemove: () => void;
  disabled?: boolean;
}

function RuleItemEditor({
  rule,
  onChange,
  onRemove,
  disabled,
}: RuleItemEditorProps) {
  const handleFieldChange = (value: string) => {
    const newField = value as RuleField;
    const validOperators = getOperatorsForField(newField);
    const currentOperatorIsValid = validOperators.includes(rule.operator);

    // Reset value when field changes, but try to preserve operator if valid
    onChange({
      field: newField,
      operator: currentOperatorIsValid
        ? rule.operator
        : getDefaultOperator(newField),
      value: "",
    });
  };

  const handleOperatorChange = (value: string) => {
    onChange({ ...rule, operator: value as RuleOperator });
  };

  const handleValueChange = (value: RuleValue) => {
    onChange({ ...rule, value });
  };

  const isValueRequired =
    rule.operator !== RuleOperator.IS_EMPTY &&
    rule.operator !== RuleOperator.IS_NOT_EMPTY;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border border-surface-a10 bg-surface-a0 p-2 shadow-sm">
      <div className="flex items-center gap-2">
        <div className="w-32 min-w-[8rem]">
          <Select
            value={rule.field}
            onChange={(e) => handleFieldChange(e.target.value)}
            disabled={disabled}
          >
            {Object.values(RuleField).map((field) => (
              <option key={field} value={field}>
                {formatEnumLabel(field)}
              </option>
            ))}
          </Select>
        </div>

        <div className="w-40 min-w-[10rem]">
          <Select
            value={rule.operator}
            onChange={(e) => handleOperatorChange(e.target.value)}
            disabled={disabled}
          >
            {getOperatorsForField(rule.field).map((op) => (
              <option key={op} value={op}>
                {formatEnumLabel(op)}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {isValueRequired && (
        <div className="min-w-[12rem] flex-1">
          <RuleValueInput
            field={rule.field}
            value={rule.value ?? null}
            onChange={handleValueChange}
            disabled={disabled}
          />
        </div>
      )}

      <Button
        variant="ghost"
        size="small"
        onClick={onRemove}
        disabled={disabled}
        className="text-text-a30 hover:text-danger-a0"
        aria-label="Remove rule"
      >
        <FaTimes />
      </Button>
    </div>
  );
}

interface RuleValueInputProps {
  field: RuleField;
  value: RuleValue;
  onChange: (value: RuleValue) => void;
  disabled?: boolean;
}

function RuleValueInput({
  field,
  value,
  onChange,
  disabled,
}: RuleValueInputProps) {
  // TODO: Implement specific inputs based on field type (Date, Number, etc.)
  // For now, using TextInput for everything
  return (
    <TextInput
      value={value?.toString() || ""}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      placeholder="Value..."
      className="h-9 py-1"
      data-field={field}
    />
  );
}

// Helpers

function formatEnumLabel(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0) + word.slice(1).toLowerCase())
    .join(" ");
}

function getDefaultOperator(field: RuleField): RuleOperator {
  switch (field) {
    case RuleField.RATING:
    case RuleField.PUBDATE:
      return RuleOperator.EQUALS;
    default:
      return RuleOperator.CONTAINS;
  }
}

function getOperatorsForField(field: RuleField): RuleOperator[] {
  const commonOps = [
    RuleOperator.EQUALS,
    RuleOperator.NOT_EQUALS,
    RuleOperator.IS_EMPTY,
    RuleOperator.IS_NOT_EMPTY,
  ];

  const stringOps = [
    RuleOperator.CONTAINS,
    RuleOperator.NOT_CONTAINS,
    RuleOperator.STARTS_WITH,
    RuleOperator.ENDS_WITH,
    RuleOperator.IN,
    RuleOperator.NOT_IN,
  ];

  const numericOps = [
    RuleOperator.GREATER_THAN,
    RuleOperator.LESS_THAN,
    RuleOperator.GREATER_THAN_OR_EQUALS,
    RuleOperator.LESS_THAN_OR_EQUALS,
  ];

  switch (field) {
    case RuleField.RATING:
    case RuleField.PUBDATE:
      return [...commonOps, ...numericOps];
    default:
      return [...commonOps, ...stringOps];
  }
}
