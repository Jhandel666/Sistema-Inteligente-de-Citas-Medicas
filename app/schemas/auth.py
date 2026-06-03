from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import RolUsuario


class UsuarioCrear(BaseModel):
    nombre_completo: str = Field(min_length=3, max_length=150)
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=128)
    rol: RolUsuario = RolUsuario.RECEPCION


class SolicitudLogin(BaseModel):
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=128)


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_completo: str
    correo: EmailStr
    rol: RolUsuario
    creado_en: datetime


class RespuestaToken(BaseModel):
    token_acceso: str
    token_refresco: str
    tipo_token: str = "bearer"


class SolicitudRefresco(BaseModel):
    token_refresco: str

# Compatibilidad de nombres antiguos mientras el proyecto queda en español.
LoginRequest = SolicitudLogin
RefreshRequest = SolicitudRefresco
TokenResponse = RespuestaToken
UserCreate = UsuarioCrear
UserResponse = UsuarioRespuesta
