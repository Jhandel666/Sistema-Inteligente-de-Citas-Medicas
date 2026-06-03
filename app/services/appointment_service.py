from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException, NotFoundException
from app.notifications.email_service import EmailService
from app.repositories.appointment_repository import RepositorioCitas
from app.repositories.doctor_repository import RepositorioMedicos
from app.repositories.inteligencia_repository import RepositorioInteligencia
from app.repositories.patient_repository import RepositorioPacientes
from app.schemas.appointment import CitaCrear, CitaActualizar
from app.services.notification_service import ServicioNotificaciones


def normalizar_fecha(fecha: datetime) -> datetime:
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=UTC)
    return fecha.astimezone(UTC)


class ServicioCitas:
    def __init__(
        self,
        repositorio_citas: RepositorioCitas,
        repositorio_pacientes: RepositorioPacientes,
        repositorio_medicos: RepositorioMedicos,
        servicio_email: EmailService,
    ) -> None:
        self.repositorio_citas = repositorio_citas
        self.repositorio_pacientes = repositorio_pacientes
        self.repositorio_medicos = repositorio_medicos
        self.servicio_notificaciones = ServicioNotificaciones(servicio_email)

    def listar_citas(self, omitir: int = 0, limite: int = 100):
        return self.repositorio_citas.listar(omitir=omitir, limite=limite)

    def obtener_cita(self, cita_id: int):
        cita = self.repositorio_citas.obtener_por_id(cita_id)
        if not cita:
            raise NotFoundException("Cita no encontrada")
        return cita

    def crear_cita(self, datos: CitaCrear):
        paciente = self.repositorio_pacientes.obtener_por_id(datos.paciente_id)
        if not paciente:
            raise NotFoundException("Paciente no encontrado")

        medico = self.repositorio_medicos.obtener_por_id(datos.medico_id)
        if not medico:
            raise NotFoundException("Médico no encontrado")

        programada_en = normalizar_fecha(datos.programada_en)

        if programada_en < datetime.now(UTC):
            raise ConflictException("No se puede agendar una cita en el pasado")

        datos.programada_en = programada_en

        conflicto = self.repositorio_citas.obtener_cita_medico_en_horario(
            medico_id=datos.medico_id,
            programada_en=programada_en,
        )
        if conflicto:
            raise ConflictException("El médico ya tiene una cita en ese horario")

        return self.repositorio_citas.crear(datos)

    def actualizar_cita(self, cita_id: int, datos: CitaActualizar):
        cita = self.obtener_cita(cita_id)
        cambios = datos.model_dump(exclude_unset=True)

        paciente_id = cambios.get("paciente_id", cita.paciente_id)
        medico_id = cambios.get("medico_id", cita.medico_id)
        programada_en = cambios.get("programada_en", cita.programada_en)

        if "paciente_id" in cambios and not self.repositorio_pacientes.obtener_por_id(paciente_id):
            raise NotFoundException("Paciente no encontrado")

        if "medico_id" in cambios and not self.repositorio_medicos.obtener_por_id(medico_id):
            raise NotFoundException("Médico no encontrado")

        if "programada_en" in cambios:
            programada_en = normalizar_fecha(programada_en)

            if programada_en < datetime.now(UTC):
                raise ConflictException("No se puede reprogramar una cita al pasado")

            cambios["programada_en"] = programada_en

        if "medico_id" in cambios or "programada_en" in cambios:
            conflicto = self.repositorio_citas.obtener_cita_medico_en_horario(
                medico_id=medico_id,
                programada_en=programada_en,
                excluir_cita_id=cita_id,
            )
            if conflicto:
                raise ConflictException("El médico ya tiene una cita en ese horario")

        return self.repositorio_citas.actualizar(cita, datos)

    def eliminar_cita(self, cita_id: int) -> None:
        cita = self.obtener_cita(cita_id)
        repo_ia = RepositorioInteligencia(self.repositorio_citas.db)
        ticket = self.repositorio_citas.obtener_ticket_por_cita_id(cita_id)
        if ticket:
            repo_ia.eliminar_notificaciones_por_ticket_id(ticket.id)
        repo_ia.eliminar_notificaciones_por_cita_id(cita_id)
        repo_ia.eliminar_prediccion_por_cita_id(cita_id)
        self.repositorio_citas.eliminar_ticket_por_cita_id(cita_id)
        try:
            self.repositorio_citas.eliminar(cita)
        except IntegrityError:
            self.repositorio_citas.db.rollback()
            raise ConflictException("No se puede eliminar la cita porque tiene un ticket asociado")

    def cancelar_cita(self, cita_id: int):
        cita = self.obtener_cita(cita_id)
        return self.repositorio_citas.cancelar_cita(cita)

    def confirmar_cita(self, cita_id: int):
        cita = self.obtener_cita(cita_id)

        ticket_existente = self.repositorio_citas.obtener_ticket_por_cita_id(cita.id)
        if ticket_existente:
            raise ConflictException("La cita ya tiene un ticket generado")

        cita = self.repositorio_citas.confirmar_cita(cita)
        codigo_ticket = f"PICHANAKI-TCK-{cita.id:06d}"
        ticket = self.repositorio_citas.crear_ticket(
            cita_id=cita.id,
            codigo=codigo_ticket,
        )
        self.servicio_notificaciones.enviar_confirmacion_ticket(
            correo_paciente=cita.paciente.correo,
            correo_medico=cita.medico.correo,
            codigo_ticket=ticket.codigo,
        )
        return ticket

    def confirmar_cita_con_notificacion(self, cita_id: int):
        cita = self.obtener_cita(cita_id)
        ticket_existente = self.repositorio_citas.obtener_ticket_por_cita_id(cita.id)
        if ticket_existente:
            raise ConflictException("La cita ya tiene un ticket generado")
        cita = self.repositorio_citas.confirmar_cita(cita)
        codigo_ticket = f"PICHANAKI-TCK-{cita.id:06d}"
        ticket = self.repositorio_citas.crear_ticket(
            cita_id=cita.id,
            codigo=codigo_ticket,
        )
        resultado_envio = self.servicio_notificaciones.enviar_confirmacion_ticket(
            correo_paciente=cita.paciente.correo,
            correo_medico=cita.medico.correo,
            codigo_ticket=ticket.codigo,
        )
        return ticket, resultado_envio

    def sugerir_horarios_disponibles(self, medico_id: int, programada_en, cantidad: int = 3) -> list[str]:
        sugerencias: list[str] = []
        programada_en = normalizar_fecha(programada_en)
        base_dia = programada_en.replace(minute=0, second=0, microsecond=0)

        candidatos = []
        for desplazamiento in [30, 60, 90, 120, -30, -60, 150, 180, 210, 240]:
            candidatos.append(base_dia + timedelta(minutes=desplazamiento))

        for candidato in candidatos:
            if candidato.date() != programada_en.date():
                continue
            if candidato.hour < 8 or candidato.hour >= 17:
                continue
            conflicto = self.repositorio_citas.obtener_cita_medico_en_horario(
                medico_id=medico_id,
                programada_en=candidato,
            )
            if not conflicto:
                etiqueta = candidato.strftime("%H:%M")
                if etiqueta not in sugerencias:
                    sugerencias.append(etiqueta)
            if len(sugerencias) >= cantidad:
                break

        return sugerencias

    def listar_tickets(self, omitir: int = 0, limite: int = 100):
        return self.repositorio_citas.listar_tickets(omitir=omitir, limite=limite)

    def obtener_ticket_por_id(self, ticket_id: int):
        ticket = self.repositorio_citas.obtener_ticket_por_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket no encontrado")
        return ticket

    def obtener_ticket_por_codigo(self, codigo: str):
        ticket = self.repositorio_citas.obtener_ticket_por_codigo(codigo)
        if not ticket:
            raise NotFoundException("Ticket no encontrado")
        return ticket


AppointmentService = ServicioCitas

ServicioCitas.list_appointments = ServicioCitas.listar_citas
ServicioCitas.get_appointment = ServicioCitas.obtener_cita
ServicioCitas.create_appointment = ServicioCitas.crear_cita
ServicioCitas.update_appointment = ServicioCitas.actualizar_cita
ServicioCitas.delete_appointment = ServicioCitas.eliminar_cita
ServicioCitas.cancel_appointment = ServicioCitas.cancelar_cita
ServicioCitas.confirm_appointment = ServicioCitas.confirmar_cita
ServicioCitas.suggest_available_slots = ServicioCitas.sugerir_horarios_disponibles
ServicioCitas.list_tickets = ServicioCitas.listar_tickets
ServicioCitas.get_ticket_by_id = ServicioCitas.obtener_ticket_por_id
ServicioCitas.get_ticket_by_code = ServicioCitas.obtener_ticket_por_codigo
