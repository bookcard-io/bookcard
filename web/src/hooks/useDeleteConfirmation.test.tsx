import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { type User, UserContext } from "@/contexts/UserContext";
import { useDeleteConfirmation } from "./useDeleteConfirmation";

type UserContextValue = React.ComponentProps<
  typeof UserContext.Provider
>["value"];

function createWrapper(mockContext: Partial<UserContextValue> = {}) {
  const defaultContext: UserContextValue = {
    user: null,
    isLoading: false,
    error: null,
    refresh: vi.fn<() => Promise<void>>(),
    refreshTimestamp: 0,
    updateUser: vi.fn<(userData: Partial<User>) => void>(),
    profilePictureUrl: null,
    invalidateProfilePictureCache: vi.fn<() => void>(),
    settings: {},
    isSaving: false,
    getSetting: vi.fn<(key: string) => string | null>(() => null),
    updateSetting: vi.fn<(key: string, value: string) => void>(),
    ...mockContext,
  };

  return ({ children }: { children: ReactNode }) => (
    <UserContext.Provider value={defaultContext}>
      {children}
    </UserContext.Provider>
  );
}

describe("useDeleteConfirmation", () => {
  let mockGetSetting: ReturnType<typeof vi.fn<(key: string) => string | null>>;
  let mockUpdateSetting: ReturnType<
    typeof vi.fn<(key: string, value: string) => void>
  >;
  let onSuccess: ReturnType<typeof vi.fn<() => void>>;
  let onError: ReturnType<typeof vi.fn<(error: string) => void>>;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();
    mockGetSetting = vi.fn<(key: string) => string | null>(() => null);
    mockUpdateSetting = vi.fn<(key: string, value: string) => void>();
    onSuccess = vi.fn<() => void>();
    onError = vi.fn<(error: string) => void>();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with closed modal", () => {
    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    expect(result.current.isOpen).toBe(false);
    expect(result.current.dontShowAgain).toBe(false);
    expect(result.current.deleteFilesFromDrive).toBe(false);
    expect(result.current.isDeleting).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should open modal when open is called", () => {
    mockGetSetting.mockReturnValue("true"); // always_warn_on_delete = true
    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.open();
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("should close modal and reset state when close is called", () => {
    mockGetSetting.mockReturnValue("true");
    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.open();
      result.current.toggleDontShowAgain();
      result.current.toggleDeleteFilesFromDrive();
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.dontShowAgain).toBe(true);
    expect(result.current.deleteFilesFromDrive).toBe(true);

    act(() => {
      result.current.close();
    });

    expect(result.current.isOpen).toBe(false);
    expect(result.current.dontShowAgain).toBe(false);
    expect(result.current.deleteFilesFromDrive).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should toggle dontShowAgain", () => {
    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.toggleDontShowAgain();
    });

    expect(result.current.dontShowAgain).toBe(true);

    act(() => {
      result.current.toggleDontShowAgain();
    });

    expect(result.current.dontShowAgain).toBe(false);
  });

  it("should toggle deleteFilesFromDrive", () => {
    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.toggleDeleteFilesFromDrive();
    });

    expect(result.current.deleteFilesFromDrive).toBe(true);

    act(() => {
      result.current.toggleDeleteFilesFromDrive();
    });

    expect(result.current.deleteFilesFromDrive).toBe(false);
  });

  it("should initialize deleteFilesFromDrive from setting when modal opens", () => {
    mockGetSetting.mockImplementation((key: string) => {
      if (key === "always_warn_on_delete") return "true";
      if (key === "default_delete_files_from_drive") return "true";
      return null;
    });

    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.open();
    });

    expect(result.current.deleteFilesFromDrive).toBe(true);
  });

  it("should initialize deleteFilesFromDrive to false when setting is false", () => {
    mockGetSetting.mockImplementation((key: string) => {
      if (key === "always_warn_on_delete") return "true";
      if (key === "default_delete_files_from_drive") return "false";
      return null;
    });

    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.open();
    });

    expect(result.current.deleteFilesFromDrive).toBe(false);
  });

  it("should initialize deleteFilesFromDrive to false when setting is null", () => {
    mockGetSetting.mockImplementation((key: string) => {
      if (key === "always_warn_on_delete") return "true";
      if (key === "default_delete_files_from_drive") return null;
      return null;
    });

    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.open();
    });

    expect(result.current.deleteFilesFromDrive).toBe(false);
  });

  it("should skip modal and delete directly when always_warn_on_delete is false", async () => {
    mockGetSetting.mockImplementation((key: string) => {
      if (key === "always_warn_on_delete") return "false";
      if (key === "default_delete_files_from_drive") return "false";
      return null;
    });

    const mockFetchResponse = {
      ok: true,
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onSuccess, onError }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await waitFor(() => {
      expect(result.current.isDeleting).toBe(false);
    });

    expect(globalThis.fetch).toHaveBeenCalledWith("/api/books/1", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ delete_files_from_drive: false }),
    });
    expect(result.current.isOpen).toBe(false);
    expect(onSuccess).toHaveBeenCalled();
  });

  it("should delete with deleteFilesFromDrive true when default setting is true", async () => {
    mockGetSetting.mockImplementation((key: string) => {
      if (key === "always_warn_on_delete") return "false";
      if (key === "default_delete_files_from_drive") return "true";
      return null;
    });

    const mockFetchResponse = {
      ok: true,
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onSuccess }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await waitFor(() => {
      expect(result.current.isDeleting).toBe(false);
    });

    expect(globalThis.fetch).toHaveBeenCalledWith("/api/books/1", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ delete_files_from_drive: true }),
    });
    expect(result.current.isOpen).toBe(false);
    expect(onSuccess).toHaveBeenCalled();
  });

  it("should delete with deleteFilesFromDrive false when default setting is empty string", async () => {
    mockGetSetting.mockImplementation((key: string) => {
      if (key === "always_warn_on_delete") return "false";
      if (key === "default_delete_files_from_drive") return "";
      return null;
    });

    const mockFetchResponse = {
      ok: true,
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onSuccess }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await waitFor(() => {
      expect(result.current.isDeleting).toBe(false);
    });

    expect(globalThis.fetch).toHaveBeenCalledWith("/api/books/1", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ delete_files_from_drive: false }),
    });
    expect(result.current.isOpen).toBe(false);
    expect(onSuccess).toHaveBeenCalled();
  });

  it("should show modal when always_warn_on_delete is null", () => {
    mockGetSetting.mockReturnValue(null);

    const { result } = renderHook(() => useDeleteConfirmation({ bookId: 1 }), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
      }),
    });

    act(() => {
      result.current.open();
    });

    expect(result.current.isOpen).toBe(true);
  });

  it("should not delete when bookId is null and open is called", () => {
    mockGetSetting.mockReturnValue("false");

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: null }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(result.current.isOpen).toBe(true);
  });

  it("should successfully delete book when confirm is called", async () => {
    mockGetSetting.mockReturnValue("true");
    const mockFetchResponse = {
      ok: true,
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onSuccess, onError }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
      result.current.toggleDeleteFilesFromDrive();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(globalThis.fetch).toHaveBeenCalledWith("/api/books/1", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ delete_files_from_drive: true }),
    });
    expect(result.current.isOpen).toBe(false);
    expect(result.current.isDeleting).toBe(false);
    expect(result.current.error).toBeNull();
    expect(onSuccess).toHaveBeenCalled();
  });

  it("should update setting when dontShowAgain is checked and confirm is called", async () => {
    mockGetSetting.mockReturnValue("true");
    const mockFetchResponse = {
      ok: true,
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onSuccess }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
      result.current.toggleDontShowAgain();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(mockUpdateSetting).toHaveBeenCalledWith(
      "always_warn_on_delete",
      "false",
    );
  });

  it("should not update setting when dontShowAgain is not checked", async () => {
    mockGetSetting.mockReturnValue("true");
    const mockFetchResponse = {
      ok: true,
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onSuccess }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(mockUpdateSetting).not.toHaveBeenCalled();
  });

  it("should handle delete error with detail message", async () => {
    mockGetSetting.mockReturnValue("true");
    const errorResponse = { detail: "Book not found" };
    const mockFetchResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue(errorResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onError }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(result.current.error).toBe("Book not found");
    expect(result.current.isDeleting).toBe(false);
    expect(result.current.isOpen).toBe(true); // Modal stays open on error
    expect(onError).toHaveBeenCalledWith("Book not found");
  });

  it("should handle delete error without detail message", async () => {
    mockGetSetting.mockReturnValue("true");
    const mockFetchResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({}),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onError }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(result.current.error).toBe("Failed to delete book");
    expect(onError).toHaveBeenCalledWith("Failed to delete book");
  });

  it("should handle fetch exception", async () => {
    mockGetSetting.mockReturnValue("true");
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onError }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.isDeleting).toBe(false);
    expect(onError).toHaveBeenCalledWith("Network error");
  });

  it("should handle fetch exception with non-Error value", async () => {
    mockGetSetting.mockReturnValue("true");
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      "String error",
    );

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: 1, onError }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(result.current.error).toBe("Failed to delete book");
    expect(onError).toHaveBeenCalledWith("Failed to delete book");
  });

  it("should handle confirm when bookId is null", async () => {
    mockGetSetting.mockReturnValue("true");

    const { result } = renderHook(
      () => useDeleteConfirmation({ bookId: null, onError }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    act(() => {
      result.current.open();
    });

    await act(async () => {
      await result.current.confirm();
    });

    expect(result.current.error).toBe("No book ID provided");
    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith("No book ID provided");
  });

  it("should maintain stable handlers", () => {
    const { result, rerender } = renderHook(
      () => useDeleteConfirmation({ bookId: 1 }),
      {
        wrapper: createWrapper({
          getSetting: mockGetSetting,
          updateSetting: mockUpdateSetting,
        }),
      },
    );

    const initialOpen = result.current.open;
    const initialClose = result.current.close;
    const initialToggleDontShowAgain = result.current.toggleDontShowAgain;
    const initialToggleDeleteFilesFromDrive =
      result.current.toggleDeleteFilesFromDrive;
    const initialConfirm = result.current.confirm;

    rerender();

    expect(result.current.open).toBe(initialOpen);
    expect(result.current.close).toBe(initialClose);
    expect(result.current.toggleDontShowAgain).toBe(initialToggleDontShowAgain);
    expect(result.current.toggleDeleteFilesFromDrive).toBe(
      initialToggleDeleteFilesFromDrive,
    );
    expect(result.current.confirm).toBe(initialConfirm);
  });
});
