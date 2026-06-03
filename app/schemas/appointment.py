from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.appointment import EstadoCita


class CitaCrear(BaseModel):
    paciente_id: int = Field(gt=0)
    medico_id: int = Field(gt=0)
    programada_en: datetime
    motivo: str = Field(min_length=5, max_length=255)


class CitaActualizar(BaseModel):
    paciente_id: int | None = Field(default=None, gt=0)
    medico_id: int | None = Field(default=None, gt=0)
    programada_en: datetime | None = None
    motivo: str | None = Field(default=None, min_length=5, max_length=255)
    estado: EstadoCita | None = None


class CitaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    medico_id: int
    programada_en: datetime
    estado: EstadoCita
    motivo: str
    creado_en: datetime


class TicketRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cita_id: int
    codigo: str
    esta_confirmado: bool
    emitido_en: datetime


class SolicitudCitaVoz(BaseModel):
    texto: str = Field(min_length=3, max_length=500)
    correo_paciente: EmailStr | None = None


class SolicitudRiesgoCita(BaseModel):
    cita_id: int | None = Field(default=None, gt=0)
    paciente_id: int | None = Field(default=None, gt=0)
    medico_id: int | None = Field(default=None, gt=0)
    edad_paciente: int = Field(..., ge=0, le=120)
    genero: str
    especialidad: str
    prioridad: str
    turno_cita: str
    conteo_inasistencias_previas: int = Field(..., ge=0)
    distancia_km: float = Field(..., ge=0)
    dias_hasta_cita: int = Field(..., ge=0)
    minutos_espera_estimados: int = Field(..., ge=0)


class RespuestaRiesgoCita(BaseModel):
    nivel_riesgo: str
    confianza: float
    modelo: str
    probabilidad_riesgo: float | None = None
    prediccion_id: int | None = None

class AsistenciaCrear(BaseModel):
    paciente_id: int = Field(gt=0)
    cita_id: int = Field(gt=0)
    asistio: bool


class AsistenciaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    cita_id: int
    asistio: bool
    creado_en: datetime

# Compatibilidad de nombres antiguos mientras el proyecto queda en español.
AppointmentCreate = CitaCrear
AppointmentUpdate = CitaActualizar
AppointmentResponse = CitaRespuesta
AppointmentRiskRequest = SolicitudRiesgoCita
AppointmentRiskResponse = RespuestaRiesgoCita
TicketResponse = TicketRespuesta
VoiceAppointmentRequest = SolicitudCitaVoz
