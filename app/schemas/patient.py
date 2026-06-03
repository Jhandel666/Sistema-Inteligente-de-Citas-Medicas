from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PacienteBase(BaseModel):
    nombres: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    numero_documento: str = Field(min_length=8, max_length=20)
    correo: EmailStr
    telefono: str = Field(min_length=9, max_length=9, pattern=r"^9\d{8}$")
    fecha_nacimiento: date
    genero: str | None = None


class PacienteCrear(PacienteBase):
    pass


class PacienteActualizar(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=100)
    apellidos: str | None = Field(default=None, min_length=2, max_length=100)
    numero_documento: str | None = Field(default=None, min_length=8, max_length=20)
    correo: EmailStr | None = None
    telefono: str | None = Field(default=None, min_length=9, max_length=9, pattern=r"^9\d{8}$")
    fecha_nacimiento: date | None = None
    genero: str | None = None


class PacienteRespuesta(PacienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creado_en: datetime

# Compatibilidad de nombres antiguos mientras el proyecto queda en español.
PatientCreate = PacienteCrear
PatientUpdate = PacienteActualizar
PatientResponse = PacienteRespuesta
