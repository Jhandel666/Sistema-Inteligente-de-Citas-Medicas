from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Paciente
from app.schemas.patient import PacienteCrear, PacienteActualizar


class RepositorioPacientes:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, omitir: int = 0, limite: int = 100) -> list[Paciente]:
        sentencia = select(Paciente).offset(omitir).limit(limite).order_by(Paciente.id.desc())
        return list(self.db.scalars(sentencia).all())

    def crear(self, datos: PacienteCrear) -> Paciente:
        paciente = Paciente(**datos.model_dump())
        self.db.add(paciente)
        self.db.commit()
        self.db.refresh(paciente)
        return paciente

    def obtener_por_id(self, paciente_id: int) -> Paciente | None:
        return self.db.get(Paciente, paciente_id)

    def obtener_por_correo(self, correo: str) -> Paciente | None:
        sentencia = select(Paciente).where(Paciente.correo == correo)
        return self.db.scalar(sentencia)

    def obtener_por_numero_documento(self, numero_documento: str) -> Paciente | None:
        sentencia = select(Paciente).where(Paciente.numero_documento == numero_documento)
        return self.db.scalar(sentencia)

    def actualizar(self, paciente: Paciente, datos: PacienteActualizar) -> Paciente:
        for clave, valor in datos.model_dump(exclude_unset=True).items():
            setattr(paciente, clave, valor)
        self.db.add(paciente)
        self.db.commit()
        self.db.refresh(paciente)
        return paciente

    def eliminar(self, paciente: Paciente) -> None:
        self.db.delete(paciente)
        self.db.commit()

# Compatibilidad con nombres anteriores en inglés.
PatientRepository = RepositorioPacientes

RepositorioPacientes.get_by_id = RepositorioPacientes.obtener_por_id
RepositorioPacientes.get_by_email = RepositorioPacientes.obtener_por_correo
RepositorioPacientes.get_by_document_number = RepositorioPacientes.obtener_por_numero_documento
RepositorioPacientes.create = RepositorioPacientes.crear
RepositorioPacientes.update = RepositorioPacientes.actualizar
RepositorioPacientes.delete = RepositorioPacientes.eliminar
RepositorioPacientes.list = RepositorioPacientes.listar
