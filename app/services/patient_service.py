from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException, NotFoundException
from app.repositories.patient_repository import RepositorioPacientes
from app.schemas.patient import PacienteCrear, PacienteActualizar


class ServicioPacientes:
    def __init__(self, repositorio: RepositorioPacientes) -> None:
        self.repositorio = repositorio

    def listar_pacientes(self, omitir: int = 0, limite: int = 100):
        return self.repositorio.listar(omitir=omitir, limite=limite)

    def obtener_paciente(self, paciente_id: int):
        paciente = self.repositorio.obtener_por_id(paciente_id)
        if not paciente:
            raise NotFoundException("Paciente no encontrado")
        return paciente

    def crear_paciente(self, datos: PacienteCrear):
        if self.repositorio.obtener_por_correo(datos.correo):
            raise ConflictException("Ya existe un paciente con ese correo")
        if self.repositorio.obtener_por_numero_documento(datos.numero_documento):
            raise ConflictException("Ya existe un paciente con ese número de documento")
        return self.repositorio.crear(datos)

    def actualizar_paciente(self, paciente_id: int, datos: PacienteActualizar):
        paciente = self.obtener_paciente(paciente_id)
        if datos.correo is not None:
            existente = self.repositorio.obtener_por_correo(datos.correo)
            if existente and existente.id != paciente_id:
                raise ConflictException("Ya existe otro paciente con ese correo")
        if datos.numero_documento is not None:
            existente = self.repositorio.obtener_por_numero_documento(datos.numero_documento)
            if existente and existente.id != paciente_id:
                raise ConflictException("Ya existe otro paciente con ese número de documento")
        return self.repositorio.actualizar(paciente, datos)

    def eliminar_paciente(self, paciente_id: int) -> None:
        paciente = self.obtener_paciente(paciente_id)
        try:
            self.repositorio.eliminar(paciente)
        except IntegrityError:
            self.repositorio.db.rollback()
            raise ConflictException("No se puede eliminar el paciente porque tiene citas registradas")

# Compatibilidad con nombres anteriores en inglés.
PatientService = ServicioPacientes

ServicioPacientes.list_patients = ServicioPacientes.listar_pacientes
ServicioPacientes.get_patient = ServicioPacientes.obtener_paciente
ServicioPacientes.create_patient = ServicioPacientes.crear_paciente
ServicioPacientes.update_patient = ServicioPacientes.actualizar_paciente
ServicioPacientes.delete_patient = ServicioPacientes.eliminar_paciente
