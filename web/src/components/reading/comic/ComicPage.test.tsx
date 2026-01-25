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

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ComicPage } from "./ComicPage";

describe("ComicPage", () => {
  it("emits onDimensions and onLoad from the rendered img", () => {
    const onLoad = vi.fn();
    const onDimensions = vi.fn();

    render(
      <ComicPage
        bookId={42}
        format="cbz"
        pageNumber={3}
        onLoad={onLoad}
        onDimensions={onDimensions}
      />,
    );

    const img = screen.getByAltText("Page 3") as HTMLImageElement;

    Object.defineProperty(img, "naturalWidth", { value: 1200 });
    Object.defineProperty(img, "naturalHeight", { value: 800 });

    fireEvent.load(img);

    expect(onDimensions).toHaveBeenCalledWith({ width: 1200, height: 800 });
    expect(onLoad).toHaveBeenCalledTimes(1);
  });

  it("shows an error message on image error", () => {
    render(<ComicPage bookId={42} format="cbz" pageNumber={3} />);

    const img = screen.getByAltText("Page 3") as HTMLImageElement;
    fireEvent.error(img);

    expect(screen.getByText("Failed to load page")).toBeInTheDocument();
  });
});
