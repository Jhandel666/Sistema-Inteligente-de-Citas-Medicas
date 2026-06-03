from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException, NotFoundException
from app.repositories.doctor_repository import RepositorioMedicos
from app.schemas.doctor import MedicoCrear, MedicoActualizar


class ServicioMedicos:
    def __init__(self, repositorio: RepositorioMedicos) -> None:
        self.repositorio = repositorio

    def listar_medicos(self, omitir: int = 0, limite: int = 100):
        return self.repositorio.listar(omitir=omitir, limite=limite)

    def obtener_medico(self, medico_id: int):
        medico = self.repositorio.obtener_por_id(medico_id)
        if not medico:
            raise NotFoundException("Médico no encontrado")
        return medico

    def crear_medico(self, datos: MedicoCrear):
        if self.repositorio.obtener_por_correo(datos.correo):
            raise ConflictException("Ya existe un médico con ese correo")
        return self.repositorio.crear(datos)

    def actualizar_medico(self, medico_id: int, datos: MedicoActualizar):
        medico = self.obtener_medico(medico_id)
        if datos.correo is not None:
            existente = self.repositorio.obtener_por_correo(datos.correo)
            if existente and existente.id != medico_id:
                raise ConflictException("Ya existe otro médico con ese correo")
        return self.repositorio.actualizar(medico, datos)

    def eliminar_medico(self, medico_id: int) -> None:
        medico = self.obtener_medico(medico_id)
        try:
            self.repositorio.eliminar(medico)
        except IntegrityError:
            self.repositorio.db.rollback()
            raise ConflictException("No se puede eliminar el médico porque tiene citas registradas")

# Compatibilidad con nombres anteriores en inglés.
DoctorService = ServicioMedicos

ServicioMedicos.list_doctors = ServicioMedicos.listar_medicos
ServicioMedicos.get_doctor = ServicioMedicos.obtener_medico
ServicioMedicos.create_doctor = ServicioMedicos.crear_medico
ServicioMedicos.update_doctor = ServicioMedicos.actualizar_medico
ServicioMedicos.delete_doctor = ServicioMedicos.eliminar_medico
