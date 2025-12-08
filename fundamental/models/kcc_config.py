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

"""KCC (Kindle Comic Converter) configuration models.

User-level configuration profiles for KCC conversion settings.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Index, Integer, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from fundamental.models.auth import User


class KCCConversionProfile(SQLModel, table=True):
    """KCC conversion profile for user-level configuration.

    Stores user preferences for comic/manga conversion using KCC,
    including device profiles, processing options, and output formats.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    user_id : int
        Foreign key to user who owns this profile.
    name : str
        Profile name (e.g., "Kindle Paperwhite 5", "Kobo Clara").
    is_default : bool
        Whether this is the user's default profile.
    device_profile : str
        KCC device profile code (e.g., 'KV', 'KPW5', 'KS', 'KoC').
        Default: 'KV' (Kindle Voyage).
    output_format : str
        Default output format preference (MOBI, EPUB, KEPUB, CBZ, PDF, KFX).
        Default: 'MOBI'.
    manga_style : bool
        Enable manga style (right-to-left reading and splitting).
        Default: False.
    hq : bool
        Try to increase quality of magnification.
        Default: False.
    two_panel : bool
        Display two panels instead of four in Panel View mode.
        Default: False.
    webtoon : bool
        Enable webtoon processing mode.
        Default: False.
    upscale : bool
        Resize images smaller than device's resolution.
        Default: False.
    stretch : bool
        Stretch images to device's resolution.
        Default: False.
    gamma : float | None
        Apply gamma correction to linearize the image.
        None means auto (default).
    autolevel : bool
        Set most common dark pixel value to be black point for leveling.
        Default: False.
    autocontrast : bool
        Enable autocontrast (default: True, so False disables it).
        Default: True.
    colorautocontrast : bool
        Force autocontrast for all pages.
        Default: False.
    cropping : int
        Cropping mode: 0=Disabled, 1=Margins, 2=Margins+page numbers.
        Default: 2.
    cropping_power : float
        Cropping power (default: 1.0).
    preserve_margin : float
        After calculating crop, "back up" a specified percentage amount.
        Default: 0.0.
    cropping_minimum : float
        Cropping minimum area ratio.
        Default: 0.0.
    inter_panel_crop : int
        Crop empty sections: 0=Disabled, 1=Horizontally, 2=Both.
        Default: 0.
    black_borders : bool
        Disable autodetection and force black borders.
        Default: False.
    white_borders : bool
        Disable autodetection and force white borders.
        Default: False.
    force_color : bool
        Don't convert images to grayscale.
        Default: False.
    force_png : bool
        Create PNG files instead of JPEG.
        Default: False.
    mozjpeg : bool
        Create JPEG files using mozJpeg.
        Default: False.
    maximize_strips : bool
        Turn 1x4 strips to 2x2 strips.
        Default: False.
    splitter : int
        Double page parsing mode: 0=Split, 1=Rotate, 2=Both.
        Default: 0.
    target_size : int | None
        Maximal size of output file in MB.
        None means use default (100MB for webtoon, 400MB for others).
    created_at : datetime
        Profile creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "kcc_conversion_profiles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    name: str = Field(max_length=255, index=True)
    is_default: bool = Field(default=False, index=True)
    device_profile: str = Field(default="KV", max_length=10)  # Default: Kindle Voyage
    output_format: str = Field(default="MOBI", max_length=10)
    manga_style: bool = Field(default=False)
    hq: bool = Field(default=False)
    two_panel: bool = Field(default=False)
    webtoon: bool = Field(default=False)
    upscale: bool = Field(default=False)
    stretch: bool = Field(default=False)
    gamma: float | None = Field(default=None)  # None = auto
    autolevel: bool = Field(default=False)
    autocontrast: bool = Field(default=True)
    colorautocontrast: bool = Field(default=False)
    cropping: int = Field(default=2)  # 0=Disabled, 1=Margins, 2=Margins+page numbers
    cropping_power: float = Field(default=1.0)
    preserve_margin: float = Field(default=0.0)
    cropping_minimum: float = Field(default=0.0)
    inter_panel_crop: int = Field(default=0)  # 0=Disabled, 1=Horizontally, 2=Both
    black_borders: bool = Field(default=False)
    white_borders: bool = Field(default=False)
    force_color: bool = Field(default=False)
    force_png: bool = Field(default=False)
    mozjpeg: bool = Field(default=False)
    maximize_strips: bool = Field(default=False)
    splitter: int = Field(default=0)  # 0=Split, 1=Rotate, 2=Both
    target_size: int | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
        index=True,
    )

    # Relationships
    user: User = Relationship(back_populates="kcc_profiles")

    __table_args__ = (
        UniqueConstraint("user_id", "is_default", name="uq_user_default_kcc_profile"),
        Index("idx_kcc_profiles_user", "user_id"),
        Index("idx_kcc_profiles_user_default", "user_id", "is_default"),
    )
