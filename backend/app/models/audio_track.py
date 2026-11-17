from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AudioTrack(Base):
    __tablename__ = "audio_tracks"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    artist: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    duration_sec: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    license_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    license_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    # По умолчанию публичное воспроизведение запрещено.
    allowed_public_playback: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    creator = relationship(
        "User",
        back_populates="tracks"
    )

    features = relationship(
        "TrackFeatures",
        back_populates="track",
        uselist=False,
        cascade="all, delete-orphan"
    )

    recommendations = relationship(
        "Recommendation",
        back_populates="track"
    )