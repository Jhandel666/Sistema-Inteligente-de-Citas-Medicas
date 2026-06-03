from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MedicoBase(BaseModel):
    nombres: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    especialidad: str = Field(min_length=3, max_length=120)
    correo: EmailStr


class MedicoCrear(MedicoBase):
    pass


class MedicoActualizar(BaseModel):
    nombres: str | None = Field(default=None, min_length=2, max_length=100)
    apellidos: str | None = Field(default=None, min_length=2, max_length=100)
    especialidad: str | None = Field(default=None, min_length=3, max_length=120)
    correo: EmailStr | None = None


class MedicoRespuesta(MedicoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creado_en: datetime

# Compatibilidad de nombres antiguos mientras el proyecto queda en español.
DoctorCreate = MedicoCrear
DoctorUpdate = MedicoActualizar
DoctorResponse = MedicoRespuesta
