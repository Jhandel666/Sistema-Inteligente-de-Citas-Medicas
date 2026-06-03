from fastapi import APIRouter, Depends, Query, Response, status

from app.api.v1.dependencies.database import DbSession
from app.repositories.doctor_repository import RepositorioMedicos
from app.schemas.doctor import MedicoCrear, MedicoRespuesta, MedicoActualizar
from app.services.doctor_service import ServicioMedicos


router = APIRouter()


def construir_servicio(db: DbSession) -> ServicioMedicos:
    return ServicioMedicos(RepositorioMedicos(db))


@router.get("/", response_model=list[MedicoRespuesta], status_code=status.HTTP_200_OK, summary="Listar médicos")
def listar_medicos(
    db: DbSession,
    omitir: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=1, le=500),
) -> list[MedicoRespuesta]:
    servicio = construir_servicio(db)
    return [MedicoRespuesta.model_validate(item) for item in servicio.listar_medicos(omitir, limite)]


@router.post("/", response_model=MedicoRespuesta, status_code=status.HTTP_201_CREATED, summary="Crear médico")
def crear_medico(
    datos: MedicoCrear,
    db: DbSession,
) -> MedicoRespuesta:
    servicio = construir_servicio(db)
    medico = servicio.crear_medico(datos)
    return MedicoRespuesta.model_validate(medico)


@router.get("/{medico_id}", response_model=MedicoRespuesta, status_code=status.HTTP_200_OK, summary="Obtener médico")
def obtener_medico(
    medico_id: int,
    db: DbSession,
) -> MedicoRespuesta:
    servicio = construir_servicio(db)
    medico = servicio.obtener_medico(medico_id)
    return MedicoRespuesta.model_validate(medico)


@router.put("/{medico_id}", response_model=MedicoRespuesta, status_code=status.HTTP_200_OK, summary="Actualizar médico")
def actualizar_medico(
    medico_id: int,
    datos: MedicoActualizar,
    db: DbSession,
) -> MedicoRespuesta:
    servicio = construir_servicio(db)
    medico = servicio.actualizar_medico(medico_id, datos)
    return MedicoRespuesta.model_validate(medico)


@router.delete("/{medico_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar médico")
def eliminar_medico(
    medico_id: int,
    db: DbSession,
) -> Response:
    servicio = construir_servicio(db)
    servicio.eliminar_medico(medico_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
