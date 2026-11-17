from sqlalchemy import (
    BigInteger,
    Float,
    String,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TrackFeatures(Base):
    __tablename__ = "track_features"

    track_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("audio_tracks.id", ondelete="CASCADE"),
        primary_key=True
    )

    tempo_bpm: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    rms_mean: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    rms_std: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    spectral_centroid_mean: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    onset_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    spectral_contrast_mean: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    mfcc_std: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    estimated_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    mode_difference: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    mode_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    valence_proxy: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    feature_version: Mapped[str] = mapped_column(
        String(30),
        default="audio_v1",
        nullable=False
    )

    analyzed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    track = relationship(
        "AudioTrack",
        back_populates="features"
    )