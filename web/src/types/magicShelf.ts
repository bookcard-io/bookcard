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
 * Types for Magic Shelf filter rules.
 * Matches backend definitions in bookcard/models/magic_shelf_rules.py
 */

export enum RuleOperator {
  EQUALS = "EQUALS",
  NOT_EQUALS = "NOT_EQUALS",
  CONTAINS = "CONTAINS",
  NOT_CONTAINS = "NOT_CONTAINS",
  STARTS_WITH = "STARTS_WITH",
  ENDS_WITH = "ENDS_WITH",
  GREATER_THAN = "GREATER_THAN",
  LESS_THAN = "LESS_THAN",
  GREATER_THAN_OR_EQUALS = "GREATER_THAN_OR_EQUALS",
  LESS_THAN_OR_EQUALS = "LESS_THAN_OR_EQUALS",
  IN = "IN",
  NOT_IN = "NOT_IN",
  IS_EMPTY = "IS_EMPTY",
  IS_NOT_EMPTY = "IS_NOT_EMPTY",
}

export enum RuleField {
  TITLE = "TITLE",
  AUTHOR = "AUTHOR",
  TAG = "TAG",
  SERIES = "SERIES",
  PUBLISHER = "PUBLISHER",
  LANGUAGE = "LANGUAGE",
  RATING = "RATING",
  PUBDATE = "PUBDATE",
  IDENTIFIER = "IDENTIFIER",
  ISBN = "ISBN",
}

export enum JoinType {
  AND = "AND",
  OR = "OR",
}

export type RuleValue = string | number | string[] | number[] | null;

export interface FilterRule {
  field: RuleField;
  operator: RuleOperator;
  value?: RuleValue;
}

export interface FilterGroup {
  join_type: JoinType;
  rules: (FilterRule | FilterGroup)[];
}

// Type guard to check if a rule is a group
export function isFilterGroup(
  rule: FilterRule | FilterGroup,
): rule is FilterGroup {
  return "join_type" in rule && "rules" in rule;
}
