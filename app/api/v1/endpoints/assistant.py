import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.v1.dependencies.auth import get_current_user, require_roles
from app.api.v1.dependencies.database import DbSession
from app.core.config import settings
from app.models.user import Usuario 
from app.notifications.email_service import EmailService
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_repository import PatientRepository
from app.services.appointment_service import AppointmentService
from app.services.assistant import AssistantService
from app.services.assistant.conversation_state import conversation_state_store
from app.services.doctor_service import DoctorService
from app.services.patient_service import PatientService


router = APIRouter()

_stt_service = None


def _get_stt_service():
    if not settings.use_ml:
        return None
    global _stt_service
    if _stt_service is None:
        from app.ml.inference.stt_service import STTService
        _stt_service = STTService()
    return _stt_service

_conversation_memory: dict[str, list[dict]] = {}
_user_context: dict[str, dict] = {}


def build_service(db: DbSession) -> AssistantService:
    patient_repo = PatientRepository(db)
    doctor_repo = DoctorRepository(db)
    appointment_repo = AppointmentRepository(db)
    email_service = EmailService()

    return AssistantService(
        patient_service=PatientService(patient_repo),
        doctor_service=DoctorService(doctor_repo),
        appointment_service=AppointmentService(
            repositorio_citas=appointment_repo,
            repositorio_pacientes=patient_repo,
            repositorio_medicos=doctor_repo,
            servicio_email=email_service,
        ),
    )


@router.post("/chat", status_code=status.HTTP_200_OK)
def assistant_chat(
    payload: dict,
    db: DbSession,
    user: Usuario = Depends(get_current_user),
    _: str = Depends(require_roles("admin", "recepcion", "doctor")),
) -> dict:
    user_name = user.nombre_completo
    user_key = str(user.id)

    text = payload.get("text", "").strip()

    if not text or len(text) < 1:
        return {
            "type": "clarification",
            "user_name": user_name,
            "message": "Por favor escribe tu consulta.",
        }

    history = _conversation_memory.get(user_key, [])
    context = _user_context.get(user_key, {})
    if not context:
        stored_state = conversation_state_store.get(user_key)
        if stored_state.intent:
            context = stored_state.as_pending_context()

    service = build_service(db)
    result = service.process_message(text, user_name=user_name, history=history, context=context)

    history.append({"role": "user", "text": text})
    history.append({"role": "assistant", "text": result.get("message", ""), "type": result.get("type"), "intent": result.get("action", result.get("intent", ""))})
    if len(history) > 20:
        history = history[-20:]
    _conversation_memory[user_key] = history

    ctx = result.pop("context", None)
    if ctx is not None:
        if ctx.get("pending"):
            _user_context[user_key] = ctx
            pending = ctx.get("pending", {})
            entities = pending.get("entities", {}) or {}
            conversation_state_store.update(
                user_key,
                intent=pending.get("intent"),
                values=entities,
                draft_appointment=entities.get("_draft_appointment"),
                risk_data=entities.get("risk_data"),
                risk_result=entities.get("risk_result"),
                waiting_decision=bool(entities.get("_draft_appointment")),
            )
        else:
            _user_context.pop(user_key, None)
            conversation_state_store.reset(user_key)

    result["user_name"] = user_name
    return result


@router.get("/form-schema/{entity}", status_code=status.HTTP_200_OK)
def assistant_form_schema(
    entity: str,
    db: DbSession,
    user: Usuario = Depends(get_current_user),
    _: str = Depends(require_roles("admin", "recepcion")),
) -> dict:
    from app.services.assistant.form_schema import get_form_schema
    try:
        return get_form_schema(entity, db)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Error al obtener schema: {str(e)}"}


@router.post("/form-submit", status_code=status.HTTP_200_OK)
def assistant_form_submit(
    payload: dict,
    db: DbSession,
    user: Usuario = Depends(get_current_user),
    _: str = Depends(require_roles("admin", "recepcion")),
) -> dict:
    entity = payload.get("entity", "")
    data = payload.get("data", {})
    user_name = user.full_name

    from app.repositories.appointment_repository import RepositorioCitas
    from app.repositories.doctor_repository import RepositorioMedicos
    from app.repositories.patient_repository import RepositorioPacientes
    from app.services.appointment_service import AppointmentService
    from app.services.doctor_service import DoctorService
    from app.services.patient_service import PatientService
    from app.notifications.email_service import EmailService
    from app.schemas.patient import PatientCreate
    from app.schemas.doctor import DoctorCreate
    from app.schemas.appointment import AppointmentCreate

    try:
        if entity == "patient":
            payload_schema = PatientCreate(**data)
            service = PatientService(PatientRepository(db))
            result = service.create_patient(payload_schema)
            return {
                "type": "success",
                "message": f"Paciente **{result.first_name} {result.last_name}** creado correctamente.\nDNI: {result.document_number}",
                "action": "crear_paciente",
                "target": "patients",
                "voice": "Paciente creado correctamente.",
            }

        elif entity == "doctor":
            payload_schema = DoctorCreate(**data)
            service = DoctorService(DoctorRepository(db))
            result = service.create_doctor(payload_schema)
            return {
                "type": "success",
                "message": f"Médico **Dr. {result.first_name} {result.last_name}** creado correctamente.\nEspecialidad: {result.specialty}",
                "action": "crear_medico",
                "target": "doctors",
                "voice": "Médico creado correctamente.",
            }

        elif entity == "appointment":
            payload_schema = AppointmentCreate(**data)
            email_service = EmailService()
            patient_repo = PatientRepository(db)
            doctor_repo = DoctorRepository(db)
            service = AppointmentService(
                repositorio_citas=AppointmentRepository(db),
                repositorio_pacientes=patient_repo,
                repositorio_medicos=doctor_repo,
                servicio_email=email_service,
            )
            result = service.create_appointment(payload_schema)
            return {
                "type": "success",
                "message": f"Cita #{result.id} agendada correctamente.",
                "action": "agendar_cita",
                "target": "appointments",
                "voice": "Cita creada correctamente.",
            }

        else:
            return {
                "type": "error",
                "message": f"Entidad desconocida: {entity}",
                "voice": "No se reconoce la entidad.",
            }

    except ValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": e.errors()},
        )

    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower() or "unique" in error_msg.lower():
            voice_msg = "El registro ya existe."
        else:
            voice_msg = f"Error al crear: {error_msg}"
        return {
            "type": "error",
            "message": f"Error: {error_msg}",
            "action": f"crear_{entity}",
            "voice": voice_msg,
        }


@router.post("/stt", status_code=status.HTTP_200_OK)
async def transcribe_audio(
    file: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
    _: str = Depends(require_roles("admin", "recepcion", "doctor")),
) -> dict:
    stt = _get_stt_service()
    if stt is None:
        return {"text": "", "error": "ML deshabilitado (USE_ML=false)"}

    audio_bytes = await file.read()
    text = stt.transcribe(audio_bytes, suffix=".wav")

    if not text:
        return {"text": "", "error": "No se pudo transcribir el audio"}

    return {"text": text}
