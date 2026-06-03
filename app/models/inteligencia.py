from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PrediccionRiesgoCita(Base):
    """Registro persistente de cada predicción de riesgo de inasistencia.

    Este modelo está alineado con el dump real `citas_medicas (5).sql`.
    No declara columnas que no existen en esa base para evitar errores de INSERT.
    """

    __tablename__ = "predicciones_riesgo_citas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cita_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("citas.id"), nullable=True, index=True)
    paciente_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("pacientes.id"), nullable=True, index=True)
    medico_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("medicos.id"), nullable=True, index=True)

    edad_paciente: Mapped[int] = mapped_column(Integer, nullable=False)
    genero: Mapped[str] = mapped_column(String(10), nullable=False)
    especialidad: Mapped[str] = mapped_column(String(120), nullable=False)
    prioridad: Mapped[str] = mapped_column(String(20), nullable=False)
    turno_cita: Mapped[str] = mapped_column(String(20), nullable=False)
    conteo_inasistencias_previas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    distancia_km: Mapped[float] = mapped_column(Float, nullable=False)
    dias_hasta_cita: Mapped[int] = mapped_column(Integer, nullable=False)
    minutos_espera_estimados: Mapped[int] = mapped_column(Integer, nullable=False)

    nivel_riesgo: Mapped[str] = mapped_column(String(20), nullable=False)
    probabilidad_riesgo: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confianza: Mapped[float | None] = mapped_column(Float, nullable=True)
    nombre_modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @property
    def modelo(self) -> str:
        return self.nombre_modelo

    @modelo.setter
    def modelo(self, valor: str) -> None:
        self.nombre_modelo = valor


class SesionAsistente(Base):
    """Memoria persistente del asistente LaIA.

    Alineado con SQL real: columnas `paso` y `esta_activa`.
    """

    __tablename__ = "sesiones_asistente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True, index=True)
    clave_sesion: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    intencion_actual: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entidad_actual: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paso: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    esta_activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def paso_actual(self) -> str | None:
        return self.paso

    @paso_actual.setter
    def paso_actual(self, valor: str | None) -> None:
        self.paso = valor

    @property
    def activa(self) -> bool:
        return self.esta_activa

    @activa.setter
    def activa(self, valor: bool) -> None:
        self.esta_activa = bool(valor)


class NotificacionCorreo(Base):
    """Bitácora de notificaciones enviadas o simuladas.

    Alineado con SQL real: `registros_notificaciones`.
    """

    __tablename__ = "registros_notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cita_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("citas.id"), nullable=True, index=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)
    correo_destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_destinatario: Mapped[str] = mapped_column(String(30), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False)
    mensaje_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    enviado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @property
    def destinatario(self) -> str:
        return self.correo_destinatario

    @destinatario.setter
    def destinatario(self, valor: str) -> None:
        self.correo_destinatario = valor

    @property
    def estado_envio(self) -> str:
        return self.estado

    @estado_envio.setter
    def estado_envio(self, valor: str) -> None:
        self.estado = valor

    @property
    def fecha_envio(self) -> datetime | None:
        return self.enviado_en

    @fecha_envio.setter
    def fecha_envio(self, valor: datetime | None) -> None:
        self.enviado_en = valor


class HistorialAsistencia(Base):
    __tablename__ = "historial_asistencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    paciente_id: Mapped[int] = mapped_column(Integer, ForeignKey("pacientes.id"), nullable=False, index=True)
    cita_id: Mapped[int] = mapped_column(Integer, ForeignKey("citas.id"), nullable=False, index=True)
    asistio: Mapped[bool] = mapped_column(Boolean, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ModeloIA(Base):
    """Registro de modelos ML/DL entrenados.

    Alineado con SQL real: `registro_modelos_ml`.
    """

    __tablename__ = "registro_modelos_ml"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre_modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    ruta_modelo: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    caracteristicas_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    metricas_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    entrenado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @property
    def activo(self) -> bool:
        return self.esta_activo

    @activo.setter
    def activo(self, valor: bool) -> None:
        self.esta_activo = bool(valor)
