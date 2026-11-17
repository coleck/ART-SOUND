from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    CheckConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'curator')",
            name="check_user_role"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="curator",
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Связи с картинами, треками и рекомендациями.
    artworks = relationship(
        "Artwork",
        back_populates="creator"
    )

    tracks = relationship(
        "AudioTrack",
        back_populates="creator"
    )

    reviewed_recommendations = relationship(
        "Recommendation",
        back_populates="reviewer"
    )