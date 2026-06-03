from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EstadoCita(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    REPROGRAMADA = "reprogramada"


class Cita(Base):
    __tablename__ = "citas"
    __table_args__ = (UniqueConstraint("medico_id", "programada_en", name="uq_medico_horario"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    paciente_id: Mapped[int] = mapped_column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicos.id"), nullable=False)
    programada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[EstadoCita] = mapped_column(
        SqlEnum(
            EstadoCita,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            native_enum=False,
            length=30,
        ),
        default=EstadoCita.PENDIENTE,
        nullable=False,
    )
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    paciente = relationship("Paciente", back_populates="citas")
    medico = relationship("Medico", back_populates="citas")
    ticket = relationship("Ticket", back_populates="cita", uselist=False)

# Compatibilidad interna para módulos antiguos del asistente.
Cita.patient_id = property(lambda self: self.paciente_id, lambda self, v: setattr(self, "paciente_id", v))
Cita.doctor_id = property(lambda self: self.medico_id, lambda self, v: setattr(self, "medico_id", v))
Cita.scheduled_at = property(lambda self: self.programada_en, lambda self, v: setattr(self, "programada_en", v))
Cita.status = property(lambda self: self.estado, lambda self, v: setattr(self, "estado", v))
Cita.reason = property(lambda self: self.motivo, lambda self, v: setattr(self, "motivo", v))
Cita.created_at = property(lambda self: self.creado_en)
Appointment = Cita
AppointmentStatus = EstadoCita
