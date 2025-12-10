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

import { describe, expect, it, vi } from "vitest";
import { noop, withDefault } from "./callbackUtils";

describe("noop", () => {
  it("should be a function that does nothing", () => {
    expect(typeof noop).toBe("function");
    expect(noop()).toBeUndefined();
  });

  it("should accept any arguments without throwing", () => {
    expect(() => noop()).not.toThrow();
    // noop doesn't accept arguments, but calling it with arguments won't throw
    expect(() => {
      // @ts-expect-error - Testing that noop can be called with any args without throwing
      noop(1, 2, 3);
    }).not.toThrow();
    expect(() => {
      // @ts-expect-error - Testing that noop can be called with any args without throwing
      noop("test", { key: "value" });
    }).not.toThrow();
  });
});

describe("withDefault", () => {
  it("should return the provided function when defined", () => {
    const fn = vi.fn((_x: number) => {
      // void function
    });

    const result = withDefault(fn);

    expect(result).toBe(fn);
    result(5);
    expect(fn).toHaveBeenCalledWith(5);
  });

  it("should return noop when function is undefined", () => {
    const result = withDefault(undefined);

    expect(result).toBe(noop);
    expect(() => result()).not.toThrow();
  });

  it("should return noop when function is null", () => {
    const result = withDefault(null as unknown as undefined);

    expect(result).toBe(noop);
    expect(() => result()).not.toThrow();
  });

  it("should preserve function signature", () => {
    const fn = vi.fn((_a: string, _b: number) => {
      // void function
    });

    const result = withDefault(fn);

    expect(typeof result).toBe("function");
    result("test", 123);
    expect(fn).toHaveBeenCalledWith("test", 123);
  });

  it("should work with functions that return void", () => {
    const fn = vi.fn(() => {
      // void function
    });

    const result = withDefault(fn);

    expect(result()).toBeUndefined();
    expect(fn).toHaveBeenCalled();
  });

  it("should work with functions that take no arguments", () => {
    const fn = vi.fn(() => {});

    const result = withDefault(fn);

    expect(result).toBe(fn);
    result();
    expect(fn).toHaveBeenCalled();
  });

  it("should work with functions that take multiple arguments", () => {
    const fn = vi.fn((_a: number, _b: string, _c: boolean) => {});

    const result = withDefault(fn);

    expect(result).toBe(fn);
    result(1, "test", true);
    expect(fn).toHaveBeenCalledWith(1, "test", true);
  });

  it("should handle async functions", async () => {
    const fn = vi.fn(async (x: number) => Promise.resolve(x * 2));

    const result = withDefault(fn);

    expect(result).toBe(fn);
    const promise = result(5);
    expect(fn).toHaveBeenCalledWith(5);
    await expect(promise).resolves.toBe(10);
  });
});
