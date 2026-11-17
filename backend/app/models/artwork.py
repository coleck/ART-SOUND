import uuid

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    SmallInteger,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Artwork(Base):
    __tablename__ = "artworks"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published')",
            name="check_artwork_status"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    artist: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    year: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    image_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    # Отдельный случайный идентификатор QR-ссылки.
    qr_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
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
        back_populates="artworks"
    )

    features = relationship(
        "ArtworkFeatures",
        back_populates="artwork",
        uselist=False,
        cascade="all, delete-orphan"
    )

    recommendations = relationship(
        "Recommendation",
        back_populates="artwork"
    )