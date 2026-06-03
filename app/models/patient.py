from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    genero: Mapped[str | None] = mapped_column(String(20), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    citas = relationship("Cita", back_populates="paciente")

# ---------------------------------------------------------------------------
# Compatibilidad interna mientras se completa la traducción total del proyecto.
# La base y los modelos principales quedan en español; estas propiedades evitan
# que módulos antiguos del asistente fallen mientras se migran progresivamente.
Paciente.first_name = property(lambda self: self.nombres, lambda self, v: setattr(self, "nombres", v))
Paciente.last_name = property(lambda self: self.apellidos, lambda self, v: setattr(self, "apellidos", v))
Paciente.document_number = property(lambda self: self.numero_documento, lambda self, v: setattr(self, "numero_documento", v))
Paciente.email = property(lambda self: self.correo, lambda self, v: setattr(self, "correo", v))
Paciente.phone = property(lambda self: self.telefono, lambda self, v: setattr(self, "telefono", v))
Paciente.birth_date = property(lambda self: self.fecha_nacimiento, lambda self, v: setattr(self, "fecha_nacimiento", v))
Paciente.gender = property(lambda self: self.genero, lambda self, v: setattr(self, "genero", v))
Paciente.created_at = property(lambda self: self.creado_en)
Patient = Paciente
