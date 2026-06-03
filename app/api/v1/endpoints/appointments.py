from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.exceptions import ConflictException

from app.api.v1.dependencies.auth import require_roles
from app.api.v1.dependencies.database import DbSession
from app.notifications.email_service import EmailService
from app.repositories.appointment_repository import RepositorioCitas
from app.repositories.doctor_repository import RepositorioMedicos
from app.repositories.patient_repository import RepositorioPacientes
from app.repositories.inteligencia_repository import RepositorioInteligencia
from app.schemas.appointment import (
    CitaCrear,
    CitaRespuesta,
    SolicitudRiesgoCita,
    RespuestaRiesgoCita,
    CitaActualizar,
    TicketRespuesta,
    SolicitudCitaVoz,
    AsistenciaCrear,
    AsistenciaRespuesta,
)
from app.services.appointment_service import ServicioCitas


router = APIRouter()


def construir_servicio(db: DbSession) -> ServicioCitas:
    return ServicioCitas(
        repositorio_citas=RepositorioCitas(db),
        repositorio_pacientes=RepositorioPacientes(db),
        repositorio_medicos=RepositorioMedicos(db),
        servicio_email=EmailService(),
    )


@router.get(
    "/",
    response_model=list[CitaRespuesta],
    status_code=status.HTTP_200_OK,
    summary="Listar citas",
)
def listar_citas(
    db: DbSession,
    omitir: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=1, le=500),
) -> list[CitaRespuesta]:
    servicio = construir_servicio(db)
    return [CitaRespuesta.model_validate(item) for item in servicio.listar_citas(omitir, limite)]


@router.post(
    "/",
    response_model=CitaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cita",
)
def crear_cita(
    datos: CitaCrear,
    db: DbSession,
) -> CitaRespuesta:
    servicio = construir_servicio(db)
    cita = servicio.crear_cita(datos)
    return CitaRespuesta.model_validate(cita)


@router.get(
    "/tickets/",
    response_model=list[TicketRespuesta],
    status_code=status.HTTP_200_OK,
    summary="Listar tickets",
)
def listar_tickets(
    db: DbSession,
    omitir: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=1, le=500),
) -> list[TicketRespuesta]:
    servicio = construir_servicio(db)
    return [TicketRespuesta.model_validate(item) for item in servicio.listar_tickets(omitir, limite)]


@router.get(
    "/tickets/codigo/{codigo}",
    response_model=TicketRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Obtener ticket por código",
)
def obtener_ticket_por_codigo(
    codigo: str,
    db: DbSession,
) -> TicketRespuesta:
    servicio = construir_servicio(db)
    ticket = servicio.obtener_ticket_por_codigo(codigo)
    return TicketRespuesta.model_validate(ticket)


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Obtener ticket por ID",
)
def obtener_ticket(
    ticket_id: int,
    db: DbSession,
) -> TicketRespuesta:
    servicio = construir_servicio(db)
    ticket = servicio.obtener_ticket_por_id(ticket_id)
    return TicketRespuesta.model_validate(ticket)


@router.post(
    "/voz/intencion",
    status_code=status.HTTP_200_OK,
    summary="Clasificar intención de voz",
)
def clasificar_intencion_voz(
    datos: SolicitudCitaVoz,
    _: str = Depends(require_roles("admin", "recepcion", "medico")),
) -> dict[str, str | float]:
    from app.ml.inference.intent_service import MedicalIntentService
    servicio = MedicalIntentService()
    return servicio.predict_intent(datos.texto)


@router.post(
    "/predecir-riesgo",
    response_model=RespuestaRiesgoCita,
    status_code=status.HTTP_200_OK,
    summary="Predecir riesgo de inasistencia",
)
def predecir_riesgo_cita(
    datos: SolicitudRiesgoCita,
    db: DbSession,
) -> RespuestaRiesgoCita:
    from app.ml.inference.risk_service import ServicioRiesgoCitas

    servicio = ServicioRiesgoCitas()

    if not servicio._model_registered:
        try:
            repo_ia = RepositorioInteligencia(db)
            repo_ia.registrar_modelo_ia(
                nombre_modelo="no_show_risk_model",
                tipo_modelo="clasificacion_binaria",
                ruta_modelo=str(servicio.model_path),
                caracteristicas_json={
                    "edad_paciente": "int",
                    "genero": "str",
                    "especialidad": "str",
                    "prioridad": "str",
                    "turno_cita": "str",
                    "conteo_inasistencias_previas": "int",
                    "distancia_km": "float",
                    "dias_hasta_cita": "int",
                    "minutos_espera_estimados": "int",
                },
            )
            servicio.__class__._model_registered = True
        except Exception:
            db.rollback()

    resultado = servicio.predecir_riesgo(
        patient_age=datos.edad_paciente,
        gender=datos.genero,
        specialty=datos.especialidad,
        priority=datos.prioridad,
        appointment_shift=datos.turno_cita,
        previous_no_show_count=datos.conteo_inasistencias_previas,
        distance_km=datos.distancia_km,
        days_until_appointment=datos.dias_hasta_cita,
        waiting_minutes_estimated=datos.minutos_espera_estimados,
    )

    # La predicción puede usarse en dos modos:
    # 1) Vinculada a un paciente/cita: se persiste en BD.
    # 2) Standalone desde el formulario: solo se devuelve el resultado.
    #
    # La BD real tiene predicciones_riesgo_citas.paciente_id como NOT NULL,
    # por eso NO se debe intentar guardar una predicción sin paciente_id.
    entrada = datos.model_dump()
    prediccion_id = None

    if datos.paciente_id:
        try:
            prediccion = repo_ia.guardar_prediccion_riesgo(
                entrada=entrada,
                salida=resultado,
                cita_id=datos.cita_id,
                paciente_id=datos.paciente_id,
                medico_id=datos.medico_id,
            )
            prediccion_id = prediccion.id
        except Exception:
            # Nunca romper la respuesta de predicción por un error de bitácora.
            # El flujo de cita sí enviará paciente_id y quedará persistido.
            db.rollback()
            prediccion_id = None

    return RespuestaRiesgoCita(
        nivel_riesgo=str(resultado.get("nivel_riesgo") or resultado.get("risk_level") or "desconocido"),
        confianza=float(resultado.get("confianza") or resultado.get("confidence") or 0),
        probabilidad_riesgo=float(resultado.get("probabilidad_riesgo") or resultado.get("confidence") or 0),
        modelo=str(resultado.get("modelo") or resultado.get("model") or "desconocido"),
        prediccion_id=prediccion_id,
    )


@router.get(
    "/{cita_id}",
    response_model=CitaRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Obtener cita",
)
def obtener_cita(
    cita_id: int,
    db: DbSession,
) -> CitaRespuesta:
    servicio = construir_servicio(db)
    cita = servicio.obtener_cita(cita_id)
    return CitaRespuesta.model_validate(cita)


@router.put(
    "/{cita_id}",
    response_model=CitaRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Actualizar cita",
)
def actualizar_cita(
    cita_id: int,
    datos: CitaActualizar,
    db: DbSession,
) -> CitaRespuesta:
    servicio = construir_servicio(db)
    cita = servicio.actualizar_cita(cita_id, datos)
    return CitaRespuesta.model_validate(cita)


@router.delete(
    "/{cita_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cita",
)
def eliminar_cita(
    cita_id: int,
    db: DbSession,
) -> Response:
    servicio = construir_servicio(db)
    servicio.eliminar_cita(cita_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{cita_id}/confirmar",
    response_model=TicketRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Confirmar cita y generar ticket",
)
def confirmar_cita(
    cita_id: int,
    db: DbSession,
) -> TicketRespuesta:
    servicio = construir_servicio(db)
    repo_ia = RepositorioInteligencia(db)

    # Regla institucional: no se confirma ni se genera ticket sin una
    # predicción IA registrada para la cita. Esto evita saltarse el flujo
    # paciente → médico → cita → predicción → decisión → ticket.
    if not repo_ia.existe_prediccion_para_cita(cita_id):
        raise ConflictException(
            "Antes de confirmar la cita y generar ticket debes registrar la predicción IA de riesgo."
        )

    ticket, resultado_envio = servicio.confirmar_cita_con_notificacion(cita_id)

    # Bitácora de notificaciones: registra el resultado real del envío SMTP.
    try:
        cita = servicio.obtener_cita(cita_id)
        repo_ia = RepositorioInteligencia(db)
        asunto_paciente = "Confirmación de cita médica - Hospital de Pichanaki"
        asunto_medico = "Nueva cita médica asignada - Hospital de Pichanaki"
        now_utc = datetime.now(UTC)
        if getattr(cita.paciente, "correo", None):
            exito, error = resultado_envio.get("paciente", (False, "sin resultado"))
            repo_ia.registrar_notificacion(
                cita_id=cita.id,
                ticket_id=ticket.id,
                destinatario=cita.paciente.correo,
                tipo_destinatario="paciente",
                asunto=asunto_paciente,
                estado_envio="enviado" if exito else "error",
                mensaje_error=error if not exito else None,
                fecha_envio=now_utc if exito else None,
            )
        if getattr(cita.medico, "correo", None):
            exito, error = resultado_envio.get("medico", (False, "sin resultado"))
            repo_ia.registrar_notificacion(
                cita_id=cita.id,
                ticket_id=ticket.id,
                destinatario=cita.medico.correo,
                tipo_destinatario="medico",
                asunto=asunto_medico,
                estado_envio="enviado" if exito else "error",
                mensaje_error=error if not exito else None,
                fecha_envio=now_utc if exito else None,
            )
    except Exception:
        # El log de notificación no debe bloquear la generación del ticket.
        pass

    return TicketRespuesta.model_validate(ticket)


@router.post(
    "/{cita_id}/cancelar",
    response_model=CitaRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Cancelar cita",
)
def cancelar_cita(
    cita_id: int,
    db: DbSession,
) -> CitaRespuesta:
    servicio = construir_servicio(db)
    cita = servicio.cancelar_cita(cita_id)
    return CitaRespuesta.model_validate(cita)


@router.post(
    "/{cita_id}/asistencia",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar asistencia del paciente",
)
def registrar_asistencia(
    cita_id: int,
    datos: AsistenciaCrear,
    db: DbSession,
) -> AsistenciaRespuesta:
    repo_ia = RepositorioInteligencia(db)
    asistencia = repo_ia.registrar_asistencia(
        paciente_id=datos.paciente_id,
        cita_id=cita_id,
        asistio=datos.asistio,
    )
    return AsistenciaRespuesta.model_validate(asistencia)
