from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import Usuario


class RepositorioUsuarios:
    def __init__(self, db: Session) -> None:
        self.db = db

    def crear(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        sentencia = select(Usuario).where(Usuario.correo == correo)
        return self.db.scalar(sentencia)

    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

# Compatibilidad con nombres anteriores en inglés.
UserRepository = RepositorioUsuarios

RepositorioUsuarios.get_by_id = RepositorioUsuarios.obtener_por_id
RepositorioUsuarios.get_by_email = RepositorioUsuarios.obtener_por_correo
RepositorioUsuarios.create = RepositorioUsuarios.crear
