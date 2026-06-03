from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Medico(Base):
    __tablename__ = "medicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    especialidad: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    citas = relationship("Cita", back_populates="medico")

# Compatibilidad interna para módulos antiguos del asistente.
Medico.first_name = property(lambda self: self.nombres, lambda self, v: setattr(self, "nombres", v))
Medico.last_name = property(lambda self: self.apellidos, lambda self, v: setattr(self, "apellidos", v))
Medico.specialty = property(lambda self: self.especialidad, lambda self, v: setattr(self, "especialidad", v))
Medico.email = property(lambda self: self.correo, lambda self, v: setattr(self, "correo", v))
Medico.created_at = property(lambda self: self.creado_en)
Doctor = Medico
