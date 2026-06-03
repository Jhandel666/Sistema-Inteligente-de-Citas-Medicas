from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.appointment import Cita, EstadoCita
from app.models.ticket import Ticket
from app.schemas.appointment import CitaCrear, CitaActualizar


class RepositorioCitas:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, omitir: int = 0, limite: int = 100) -> list[Cita]:
        sentencia = (
            select(Cita)
            .order_by(Cita.id.desc())
            .offset(omitir)
            .limit(limite)
        )
        return list(self.db.scalars(sentencia).all())

    def listar_por_estado(self, estado: EstadoCita, omitir: int = 0, limite: int = 100) -> list[Cita]:
        sentencia = (
            select(Cita)
            .where(Cita.estado == estado)
            .order_by(Cita.programada_en.desc())
            .offset(omitir)
            .limit(limite)
        )
        return list(self.db.scalars(sentencia).all())

    def listar_proximas(self, limite: int = 10) -> list[Cita]:
        sentencia = (
            select(Cita)
            .where(Cita.programada_en >= datetime.now(UTC))
            .where(Cita.estado.in_([EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]))
            .order_by(Cita.programada_en.asc())
            .limit(limite)
        )
        return list(self.db.scalars(sentencia).all())

    def listar_por_paciente(self, paciente_id: int, omitir: int = 0, limite: int = 100) -> list[Cita]:
        sentencia = (
            select(Cita)
            .where(Cita.paciente_id == paciente_id)
            .order_by(Cita.programada_en.desc())
            .offset(omitir)
            .limit(limite)
        )
        return list(self.db.scalars(sentencia).all())

    def listar_por_medico(self, medico_id: int, omitir: int = 0, limite: int = 100) -> list[Cita]:
        sentencia = (
            select(Cita)
            .where(Cita.medico_id == medico_id)
            .order_by(Cita.programada_en.desc())
            .offset(omitir)
            .limit(limite)
        )
        return list(self.db.scalars(sentencia).all())

    def contar(self) -> int:
        sentencia = select(func.count()).select_from(Cita)
        return int(self.db.scalar(sentencia) or 0)

    def contar_por_estado(self, estado: EstadoCita) -> int:
        sentencia = (
            select(func.count())
            .select_from(Cita)
            .where(Cita.estado == estado)
        )
        return int(self.db.scalar(sentencia) or 0)

    def contar_tickets(self) -> int:
        sentencia = select(func.count()).select_from(Ticket)
        return int(self.db.scalar(sentencia) or 0)

    def crear(self, datos: CitaCrear) -> Cita:
        cita = Cita(**datos.model_dump())
        self.db.add(cita)
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def obtener_por_id(self, cita_id: int) -> Cita | None:
        return self.db.get(Cita, cita_id)

    def obtener_cita_medico_en_horario(
        self,
        medico_id: int,
        programada_en: datetime,
        excluir_cita_id: int | None = None,
    ) -> Cita | None:
        sentencia = select(Cita).where(
            Cita.medico_id == medico_id,
            Cita.programada_en == programada_en,
            Cita.estado.in_([EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]),
        )
        if excluir_cita_id is not None:
            sentencia = sentencia.where(Cita.id != excluir_cita_id)
        return self.db.scalar(sentencia)

    def obtener_citas_medico_en_fecha(self, medico_id: int, fecha: datetime) -> list[Cita]:
        inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
        sentencia = (
            select(Cita)
            .where(
                Cita.medico_id == medico_id,
                Cita.programada_en >= inicio,
                Cita.programada_en <= fin,
                Cita.estado.in_([EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]),
            )
            .order_by(Cita.programada_en)
        )
        return list(self.db.scalars(sentencia).all())

    def actualizar(self, cita: Cita, datos: CitaActualizar) -> Cita:
        for clave, valor in datos.model_dump(exclude_unset=True).items():
            setattr(cita, clave, valor)
        self.db.add(cita)
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def reprogramar(self, cita: Cita, programada_en: datetime) -> Cita:
        cita.programada_en = programada_en
        cita.estado = EstadoCita.REPROGRAMADA
        self.db.add(cita)
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def eliminar(self, cita: Cita) -> None:
        self.db.delete(cita)
        self.db.commit()

    def confirmar_cita(self, cita: Cita) -> Cita:
        cita.estado = EstadoCita.CONFIRMADA
        self.db.add(cita)
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def cancelar_cita(self, cita: Cita) -> Cita:
        cita.estado = EstadoCita.CANCELADA
        self.db.add(cita)
        self.db.commit()
        self.db.refresh(cita)
        return cita

    def crear_ticket(self, cita_id: int, codigo: str) -> Ticket:
        ticket = Ticket(cita_id=cita_id, codigo=codigo, esta_confirmado=True)
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def obtener_ticket_por_cita_id(self, cita_id: int) -> Ticket | None:
        sentencia = select(Ticket).where(Ticket.cita_id == cita_id)
        return self.db.scalar(sentencia)

    def listar_tickets(self, omitir: int = 0, limite: int = 100) -> list[Ticket]:
        sentencia = (
            select(Ticket)
            .order_by(Ticket.id.desc())
            .offset(omitir)
            .limit(limite)
        )
        return list(self.db.scalars(sentencia).all())

    def obtener_ticket_por_id(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def obtener_ticket_por_codigo(self, codigo: str) -> Ticket | None:
        sentencia = select(Ticket).where(Ticket.codigo == codigo)
        return self.db.scalar(sentencia)

    def eliminar_ticket_por_cita_id(self, cita_id: int) -> Ticket | None:
        ticket = self.obtener_ticket_por_cita_id(cita_id)
        if not ticket:
            return None
        deleted_id = ticket.id
        self.db.delete(ticket)
        self.db.commit()
        self._reajustar_auto_increment_tickets(deleted_id)
        return ticket

    def _reajustar_auto_increment_tickets(self, deleted_id: int) -> None:
        if self.db.bind and "postgresql" in self.db.bind.dialect.name:
            self.db.execute(
                text(f"ALTER SEQUENCE tickets_id_seq RESTART WITH {deleted_id}")
            )
            self.db.commit()
        elif self.db.bind and "mysql" in self.db.bind.dialect.name:
            sentencia_max = select(func.max(Ticket.id))
            max_id = self.db.scalar(sentencia_max)
            if max_id is None or deleted_id > max_id:
                self.db.execute(text(f"ALTER TABLE tickets AUTO_INCREMENT = {deleted_id}"))
                self.db.commit()

# Compatibilidad con nombres anteriores en inglés.
AppointmentRepository = RepositorioCitas

RepositorioCitas.get_by_id = RepositorioCitas.obtener_por_id
RepositorioCitas.create = RepositorioCitas.crear
RepositorioCitas.update = RepositorioCitas.actualizar
RepositorioCitas.delete = RepositorioCitas.eliminar
RepositorioCitas.list = RepositorioCitas.listar
RepositorioCitas.get_ticket_by_id = RepositorioCitas.obtener_ticket_por_id
RepositorioCitas.get_ticket_by_code = RepositorioCitas.obtener_ticket_por_codigo
RepositorioCitas.get_ticket_by_appointment_id = RepositorioCitas.obtener_ticket_por_cita_id
