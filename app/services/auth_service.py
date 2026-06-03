from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import Usuario
from app.repositories.user_repository import RepositorioUsuarios
from app.schemas.auth import SolicitudLogin, RespuestaToken, UsuarioCrear

from app.core.config import settings
from jose import JWTError, jwt


class ServicioAuth:
    def __init__(self, repositorio: RepositorioUsuarios | None = None) -> None:
        self.repositorio = repositorio

    def registrar_usuario(self, datos: UsuarioCrear) -> Usuario:
        if self.repositorio is None:
            raise RuntimeError("RepositorioUsuarios requerido")

        if self.repositorio.obtener_por_correo(datos.correo):
            raise ConflictException("Ya existe un usuario con ese correo")

        usuario = Usuario(
            nombre_completo=datos.nombre_completo,
            correo=datos.correo,
            contrasena_hash=hash_password(datos.contrasena),
            rol=datos.rol,
        )

        return self.repositorio.crear(usuario)

    def login(self, datos: SolicitudLogin) -> RespuestaToken:
        if self.repositorio is None:
            raise RuntimeError("RepositorioUsuarios requerido")

        usuario = self.repositorio.obtener_por_correo(datos.correo)

        if not usuario or not verify_password(datos.contrasena, usuario.contrasena_hash):
            raise UnauthorizedException("Credenciales inválidas")

        rol = self._normalizar_rol(usuario.rol)

        return self.emitir_tokens(
            sujeto=str(usuario.id),
            rol=rol,
            nombre=usuario.nombre_completo,
            correo=usuario.correo,
        )

    def emitir_tokens(self, sujeto: str, rol: str, nombre: str = "", correo: str = "") -> RespuestaToken:
        return RespuestaToken(
            token_acceso=create_access_token(
                subject=sujeto,
                role=rol,
                name=nombre,
                email=correo,
            ),
            token_refresco=create_refresh_token(
                subject=sujeto,
                role=rol,
                name=nombre,
                email=correo,
            ),
        )

    def refrescar_token(self, token_refresco: str) -> RespuestaToken:
        try:
            payload = jwt.decode(
                token_refresco,
                settings.jwt_refresh_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            usuario_id = payload.get("sub")
            tipo_token = payload.get("type")
            if usuario_id is None or tipo_token != "refresh":
                raise UnauthorizedException("Token de refresco inválido")
            if self.repositorio is None:
                raise RuntimeError("RepositorioUsuarios requerido")
            usuario = self.repositorio.obtener_por_id(int(usuario_id))
            if usuario is None:
                raise UnauthorizedException("Usuario no encontrado")
            rol = self._normalizar_rol(usuario.rol)
            return self.emitir_tokens(
                sujeto=str(usuario.id),
                rol=rol,
                nombre=usuario.nombre_completo,
                correo=usuario.correo,
            )
        except JWTError:
            raise UnauthorizedException("Token de refresco inválido o expirado")

    def _normalizar_rol(self, rol: object) -> str:
        rol_raw = rol.value if hasattr(rol, "value") else str(rol)
        mapa_roles = {
            "admin": "admin",
            "administrator": "admin",
            "recepcion": "recepcion",
            "reception": "recepcion",
            "receptionist": "recepcion",
            "medico": "medico",
            "doctor": "medico",
            "paciente": "paciente",
            "patient": "paciente",
        }
        return mapa_roles.get(rol_raw.lower(), rol_raw.lower())
