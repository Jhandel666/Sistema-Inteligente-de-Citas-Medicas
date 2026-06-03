from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor import Medico
from app.schemas.doctor import MedicoCrear, MedicoActualizar


class RepositorioMedicos:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, omitir: int = 0, limite: int = 100) -> list[Medico]:
        sentencia = select(Medico).offset(omitir).limit(limite).order_by(Medico.id.desc())
        return list(self.db.scalars(sentencia).all())

    def crear(self, datos: MedicoCrear) -> Medico:
        medico = Medico(**datos.model_dump())
        self.db.add(medico)
        self.db.commit()
        self.db.refresh(medico)
        return medico

    def obtener_por_id(self, medico_id: int) -> Medico | None:
        return self.db.get(Medico, medico_id)

    def obtener_por_correo(self, correo: str) -> Medico | None:
        sentencia = select(Medico).where(Medico.correo == correo)
        return self.db.scalar(sentencia)

    def actualizar(self, medico: Medico, datos: MedicoActualizar) -> Medico:
        for clave, valor in datos.model_dump(exclude_unset=True).items():
            setattr(medico, clave, valor)
        self.db.add(medico)
        self.db.commit()
        self.db.refresh(medico)
        return medico

    def eliminar(self, medico: Medico) -> None:
        self.db.delete(medico)
        self.db.commit()

# Compatibilidad con nombres anteriores en inglés.
DoctorRepository = RepositorioMedicos

RepositorioMedicos.get_by_id = RepositorioMedicos.obtener_por_id
RepositorioMedicos.get_by_email = RepositorioMedicos.obtener_por_correo
RepositorioMedicos.create = RepositorioMedicos.crear
RepositorioMedicos.update = RepositorioMedicos.actualizar
RepositorioMedicos.delete = RepositorioMedicos.eliminar
RepositorioMedicos.list = RepositorioMedicos.listar
