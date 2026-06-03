from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RolUsuario(str, Enum):
    ADMIN = "admin"
    RECEPCION = "recepcion"
    MEDICO = "medico"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        SqlEnum(
            RolUsuario,
            values_callable=lambda enum_class: [item.value for item in enum_class],
            native_enum=False,
            length=30,
        ),
        default=RolUsuario.RECEPCION,
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

# Compatibilidad interna para módulos antiguos del asistente/autenticación.
Usuario.full_name = property(lambda self: self.nombre_completo, lambda self, v: setattr(self, "nombre_completo", v))
Usuario.email = property(lambda self: self.correo, lambda self, v: setattr(self, "correo", v))
Usuario.password_hash = property(lambda self: self.contrasena_hash, lambda self, v: setattr(self, "contrasena_hash", v))
Usuario.role = property(lambda self: self.rol, lambda self, v: setattr(self, "rol", v))
Usuario.created_at = property(lambda self: self.creado_en)
User = Usuario
UserRole = RolUsuario
