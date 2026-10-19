from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PendingVoiceCommand(Base):
    __tablename__ = "pending_voice_commands"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        index=True,
        nullable=False,
    )

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("owners.id"),
        index=True,
        nullable=True,
    )

    original_text: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    extracted_command: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    prepared_confirmation: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING_CONFIRMATION",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )