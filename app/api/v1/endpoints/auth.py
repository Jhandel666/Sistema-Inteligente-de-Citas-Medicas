from fastapi import APIRouter, HTTPException, status

from app.api.v1.dependencies.database import DbSession
from app.repositories.user_repository import RepositorioUsuarios
from app.schemas.auth import (
    SolicitudLogin,
    SolicitudRefresco,
    RespuestaToken,
    UsuarioCrear,
    UsuarioRespuesta,
)
from app.services.auth_service import ServicioAuth


router = APIRouter()


def _valor(*valores):
    """Retorna el primer valor no vacío. Evita que Pydantic reciba None."""
    for valor in valores:
        if valor is None:
            continue
        if isinstance(valor, str) and not valor.strip():
            continue
        return valor
    return None


def _normalizar_usuario_crear(datos: dict) -> dict:
    """Acepta entrada en español y compatibilidad anterior en inglés."""
    return {
        "nombre_completo": _valor(datos.get("nombre_completo"), datos.get("full_name"), datos.get("name"), datos.get("nombre")),
        "correo": _valor(datos.get("correo"), datos.get("email"), datos.get("correo_electronico"), datos.get("username")),
        "contrasena": _valor(datos.get("contrasena"), datos.get("contraseña"), datos.get("contrasenia"), datos.get("password")),
        "rol": _valor(datos.get("rol"), datos.get("role")) or "recepcion",
    }


def _normalizar_login(datos: dict) -> dict:
    """Acepta correo/contrasena y email/password."""
    return {
        "correo": _valor(datos.get("correo"), datos.get("email"), datos.get("correo_electronico"), datos.get("username"), datos.get("usuario")),
        "contrasena": _valor(datos.get("contrasena"), datos.get("contraseña"), datos.get("contrasenia"), datos.get("password"), datos.get("clave")),
    }


def _normalizar_refresco(datos: dict) -> dict:
    """Acepta token_refresco y refresh_token."""
    return {
        "token_refresco": _valor(datos.get("token_refresco"), datos.get("refresh_token"), datos.get("refresco")),
    }


def _respuesta_tokens_compatible(tokens: RespuestaToken) -> dict:
    """Devuelve campos en español y alias en inglés para no romper frontend viejo."""
    return {
        "token_acceso": tokens.token_acceso,
        "token_refresco": tokens.token_refresco,
        "tipo_token": tokens.tipo_token,
        "access_token": tokens.token_acceso,
        "refresh_token": tokens.token_refresco,
        "token_type": tokens.tipo_token,
    }


@router.post(
    "/registrar",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
)
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def registrar_usuario(datos: dict, db: DbSession) -> UsuarioRespuesta:
    try:
        datos_normalizados = UsuarioCrear(**_normalizar_usuario_crear(datos or {}))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Datos de registro incompletos. Se requiere nombre_completo, correo y contrasena.",
        ) from exc

    servicio = ServicioAuth(RepositorioUsuarios(db))
    usuario = servicio.registrar_usuario(datos_normalizados)
    return UsuarioRespuesta.model_validate(usuario)


@router.post(
    "/ingresar",
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
)
@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def ingresar(datos: dict, db: DbSession) -> dict:
    try:
        datos_normalizados = SolicitudLogin(**_normalizar_login(datos or {}))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Datos de login incompletos. Envía correo/email y contrasena/password.",
        ) from exc

    servicio = ServicioAuth(RepositorioUsuarios(db))
    tokens = servicio.login(datos_normalizados)
    return _respuesta_tokens_compatible(tokens)


@router.post(
    "/refrescar",
    status_code=status.HTTP_200_OK,
    summary="Refrescar token",
)
@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def refrescar_token(datos: dict, db: DbSession) -> dict:
    try:
        datos_normalizados = SolicitudRefresco(**_normalizar_refresco(datos or {}))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Token de refresco faltante.",
        ) from exc

    servicio = ServicioAuth(RepositorioUsuarios(db))
    tokens = servicio.refrescar_token(datos_normalizados.token_refresco)
    return _respuesta_tokens_compatible(tokens)
