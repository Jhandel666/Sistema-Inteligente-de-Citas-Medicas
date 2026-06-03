from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.api.v1.dependencies.database import DbSession
from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.models.user import Usuario
from app.repositories.user_repository import RepositorioUsuarios


security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DbSession,
) -> Usuario:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        usuario_id = payload.get("sub")
        tipo_token = payload.get("type")

        if usuario_id is None or tipo_token != "access":
            raise UnauthorizedException("Token inválido")

    except JWTError as exc:
        raise UnauthorizedException("Token inválido") from exc

    repositorio = RepositorioUsuarios(db)
    usuario = repositorio.obtener_por_id(int(usuario_id))

    if usuario is None:
        raise UnauthorizedException("Usuario no encontrado")

    return usuario


def get_current_role(
    current_user: Annotated[Usuario, Depends(get_current_user)],
) -> str:
    rol = current_user.rol
    rol_texto = rol.value if hasattr(rol, "value") else str(rol)

    mapa_roles = {
        "admin": "admin",
        "administrador": "admin",
        "recepcion": "recepcion",
        "recepción": "recepcion",
        "medico": "doctor",
        "médico": "doctor",
        "doctor": "doctor",
        "paciente": "patient",
    }

    return mapa_roles.get(rol_texto.lower(), rol_texto.lower())


def require_roles(*roles_permitidos: str):
    def verificador_roles(
        current_role: Annotated[str, Depends(get_current_role)],
    ) -> str:
        roles_normalizados = [rol.lower() for rol in roles_permitidos]

        if current_role not in roles_normalizados:
            raise ForbiddenException("No tienes permisos para realizar esta acción")

        return current_role

    return verificador_roles