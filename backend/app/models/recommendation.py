
from sqlalchemy import (
    BigInteger,
    String,
    Numeric,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="check_recommendation_score"
        ),

        CheckConstraint(
            "status IN ('proposed', 'approved', 'rejected')",
            name="check_recommendation_status"
        ),

        UniqueConstraint(
            "artwork_id",
            "track_id",
            "algorithm_version",
            name="uq_artwork_track_algorithm"
        ),

        Index(
            "uq_one_approved_per_artwork",
            "artwork_id",
            unique=True,
            postgresql_where=text("status = 'approved'")
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    artwork_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("artworks.id", ondelete="CASCADE"),
        nullable=False
    )

    track_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("audio_tracks.id", ondelete="CASCADE"),
        nullable=False
    )

    score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False
    )

    algorithm_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="proposed",
        nullable=False
    )

    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    reviewed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    artwork = relationship(
        "Artwork",
        back_populates="recommendations"
    )

    track = relationship(
        "AudioTrack",
        back_populates="recommendations"
    )

    reviewer = relationship(
        "User",
        back_populates="reviewed_recommendations"
    )
