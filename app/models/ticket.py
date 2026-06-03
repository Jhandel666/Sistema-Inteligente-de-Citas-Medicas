from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cita_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("citas.id"),
        unique=True,
        nullable=False,
    )
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    esta_confirmado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    emitido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cita = relationship("Cita", back_populates="ticket")

# Compatibilidad interna para módulos antiguos del asistente.
Ticket.appointment_id = property(lambda self: self.cita_id, lambda self, v: setattr(self, "cita_id", v))
Ticket.code = property(lambda self: self.codigo, lambda self, v: setattr(self, "codigo", v))
Ticket.is_confirmed = property(lambda self: self.esta_confirmado, lambda self, v: setattr(self, "esta_confirmado", v))
Ticket.issued_at = property(lambda self: self.emitido_en)
