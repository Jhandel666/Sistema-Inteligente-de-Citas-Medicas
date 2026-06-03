from fastapi import APIRouter, Depends, Query, Response, status

from app.api.v1.dependencies.database import DbSession
from app.repositories.patient_repository import RepositorioPacientes
from app.schemas.patient import PacienteCrear, PacienteRespuesta, PacienteActualizar
from app.services.patient_service import ServicioPacientes


router = APIRouter()


def construir_servicio(db: DbSession) -> ServicioPacientes:
    return ServicioPacientes(RepositorioPacientes(db))


@router.get("/", response_model=list[PacienteRespuesta], status_code=status.HTTP_200_OK, summary="Listar pacientes")
def listar_pacientes(
    db: DbSession,
    omitir: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=1, le=500),
) -> list[PacienteRespuesta]:
    servicio = construir_servicio(db)
    return [PacienteRespuesta.model_validate(item) for item in servicio.listar_pacientes(omitir, limite)]


@router.post("/", response_model=PacienteRespuesta, status_code=status.HTTP_201_CREATED, summary="Crear paciente")
def crear_paciente(
    datos: PacienteCrear,
    db: DbSession,
) -> PacienteRespuesta:
    servicio = construir_servicio(db)
    paciente = servicio.crear_paciente(datos)
    return PacienteRespuesta.model_validate(paciente)


@router.get("/{paciente_id}", response_model=PacienteRespuesta, status_code=status.HTTP_200_OK, summary="Obtener paciente")
def obtener_paciente(
    paciente_id: int,
    db: DbSession,
) -> PacienteRespuesta:
    servicio = construir_servicio(db)
    paciente = servicio.obtener_paciente(paciente_id)
    return PacienteRespuesta.model_validate(paciente)


@router.put("/{paciente_id}", response_model=PacienteRespuesta, status_code=status.HTTP_200_OK, summary="Actualizar paciente")
def actualizar_paciente(
    paciente_id: int,
    datos: PacienteActualizar,
    db: DbSession,
) -> PacienteRespuesta:
    servicio = construir_servicio(db)
    paciente = servicio.actualizar_paciente(paciente_id, datos)
    return PacienteRespuesta.model_validate(paciente)


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar paciente")
def eliminar_paciente(
    paciente_id: int,
    db: DbSession,
) -> Response:
    servicio = construir_servicio(db)
    servicio.eliminar_paciente(paciente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
