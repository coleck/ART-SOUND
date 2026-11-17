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


class ArtworkFeatures(Base):
    __tablename__ = "artwork_features"

    artwork_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("artworks.id", ondelete="CASCADE"),
        primary_key=True
    )

    brightness: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    contrast: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    saturation: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    edge_density: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    color_entropy: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    valence_proxy: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    feature_version: Mapped[str] = mapped_column(
        String(30),
        default="image_v1",
        nullable=False
    )

    analyzed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    artwork = relationship(
        "Artwork",
        back_populates="features"
    )