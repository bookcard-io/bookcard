# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""KCC profile API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KCCProfileRead(BaseModel):
    """KCC conversion profile read schema.

    Attributes
    ----------
    id : int
        Profile ID.
    user_id : int
        User ID who owns the profile.
    name : str
        Profile name.
    is_default : bool
        Whether this is the default profile.
    device_profile : str
        KCC device profile code.
    output_format : str
        Default output format.
    manga_style : bool
        Enable manga style.
    hq : bool
        High quality mode.
    two_panel : bool
        Two panel mode.
    webtoon : bool
        Webtoon mode.
    upscale : bool
        Upscale images.
    stretch : bool
        Stretch images.
    gamma : float | None
        Gamma correction value.
    autolevel : bool
        Auto leveling.
    autocontrast : bool
        Auto contrast.
    colorautocontrast : bool
        Color auto contrast.
    cropping : int
        Cropping mode.
    cropping_power : float
        Cropping power.
    preserve_margin : float
        Preserve margin percentage.
    cropping_minimum : float
        Cropping minimum area ratio.
    inter_panel_crop : int
        Inter-panel crop mode.
    black_borders : bool
        Force black borders.
    white_borders : bool
        Force white borders.
    force_color : bool
        Force color mode.
    force_png : bool
        Force PNG output.
    mozjpeg : bool
        Use mozJpeg.
    maximize_strips : bool
        Maximize strips.
    splitter : int
        Splitter mode.
    target_size : int | None
        Target file size in MB.
    created_at : datetime
        Creation timestamp.
    updated_at : datetime
        Update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    is_default: bool
    device_profile: str
    output_format: str
    manga_style: bool
    hq: bool
    two_panel: bool
    webtoon: bool
    upscale: bool
    stretch: bool
    gamma: float | None = None
    autolevel: bool
    autocontrast: bool
    colorautocontrast: bool
    cropping: int
    cropping_power: float
    preserve_margin: float
    cropping_minimum: float
    inter_panel_crop: int
    black_borders: bool
    white_borders: bool
    force_color: bool
    force_png: bool
    mozjpeg: bool
    maximize_strips: bool
    splitter: int
    target_size: int | None = None
    created_at: datetime
    updated_at: datetime


class KCCProfileCreate(BaseModel):
    """KCC profile creation schema."""

    name: str = Field(min_length=1, max_length=255)
    is_default: bool = False
    device_profile: str = Field(default="KV", max_length=10)
    output_format: str = Field(default="MOBI", max_length=10)
    manga_style: bool = False
    hq: bool = False
    two_panel: bool = False
    webtoon: bool = False
    upscale: bool = False
    stretch: bool = False
    gamma: float | None = None
    autolevel: bool = False
    autocontrast: bool = True
    colorautocontrast: bool = False
    cropping: int = Field(default=2, ge=0, le=2)
    cropping_power: float = Field(default=1.0, ge=0.0)
    preserve_margin: float = Field(default=0.0, ge=0.0)
    cropping_minimum: float = Field(default=0.0, ge=0.0)
    inter_panel_crop: int = Field(default=0, ge=0, le=2)
    black_borders: bool = False
    white_borders: bool = False
    force_color: bool = False
    force_png: bool = False
    mozjpeg: bool = False
    maximize_strips: bool = False
    splitter: int = Field(default=0, ge=0, le=2)
    target_size: int | None = Field(default=None, ge=1)


class KCCProfileUpdate(BaseModel):
    """KCC profile update schema."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_default: bool | None = None
    device_profile: str | None = Field(default=None, max_length=10)
    output_format: str | None = Field(default=None, max_length=10)
    manga_style: bool | None = None
    hq: bool | None = None
    two_panel: bool | None = None
    webtoon: bool | None = None
    upscale: bool | None = None
    stretch: bool | None = None
    gamma: float | None = None
    autolevel: bool | None = None
    autocontrast: bool | None = None
    colorautocontrast: bool | None = None
    cropping: int | None = Field(default=None, ge=0, le=2)
    cropping_power: float | None = Field(default=None, ge=0.0)
    preserve_margin: float | None = Field(default=None, ge=0.0)
    cropping_minimum: float | None = Field(default=None, ge=0.0)
    inter_panel_crop: int | None = Field(default=None, ge=0, le=2)
    black_borders: bool | None = None
    white_borders: bool | None = None
    force_color: bool | None = None
    force_png: bool | None = None
    mozjpeg: bool | None = None
    maximize_strips: bool | None = None
    splitter: int | None = Field(default=None, ge=0, le=2)
    target_size: int | None = Field(default=None, ge=1)
