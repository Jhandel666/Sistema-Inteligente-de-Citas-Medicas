from __future__ import annotations

import re
from datetime import UTC, date, datetime

from app.core.exceptions import NotFoundException, ConflictException
from app.schemas.appointment import AppointmentCreate
from app.schemas.patient import PatientUpdate
from app.services.appointment_service import AppointmentService
from app.services.assistant.patient_actions import PatientActions
from app.services.assistant.doctor_actions import DoctorActions
from app.services.assistant.intent_detector import extraer_datos_paciente, extraer_datos_medico, fmt_estado


class AppointmentActions:
    def __init__(
        self,
        appointment_service: AppointmentService,
        patient_actions: PatientActions,
        doctor_actions: DoctorActions,
    ) -> None:
        self.service = appointment_service
        self.patient_actions = patient_actions
        self.doctor_actions = doctor_actions
        self._risk_service = None

    def _get_risk_service(self):
        if self._risk_service is None:
            try:
                from app.ml.inference.risk_service import AppointmentRiskService
                self._risk_service = AppointmentRiskService()
            except Exception:
                self._risk_service = False
        return self._risk_service if self._risk_service is not False else None

    def _count_previous_no_shows(self, patient_id: int) -> int:
        """Cuenta citas previas canceladas del paciente como proxy de faltas."""
        try:
            citas = self.service.list_appointments(limit=500)
            return sum(
                1 for a in citas
                if a.patient_id == patient_id
                and a.status in ("cancelled", "CANCELLED")
            )
        except Exception:
            return 0

    def _infer_priority(self, reason: str | None) -> str:
        """Infiere prioridad (baja/media/alta) del motivo de consulta."""
        if not reason:
            return "media"
        r = reason.lower()
        if any(w in r for w in ["emergencia", "urgencia", "grave", "dolor intenso", "accidente"]):
            return "alta"
        if any(w in r for w in ["control", "resultado", "receta", "revision", "rutina"]):
            return "baja"
        return "media"


    def _is_only_time_or_date(self, text: str) -> bool:
        """Evita usar frases de hora/fecha como motivo de consulta."""
        t = text.lower().strip().rstrip(".,;")
        time_patterns = [
            r"^(?:a\s+)?(?:las?\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm|horas?|hrs?)?$",
            r"^\d{1,2}(?::\d{2})?\s*(?:am|pm|horas?|hrs?)?$",
        ]
        date_patterns = [
            r"^(?:para\s+)?(?:el\s+)?\d{1,2}\s+de\s+[a-záéíóúñ]+(?:\s+(?:del?|de)\s+\d{4})?$",
            r"^(?:para\s+)?(?:el\s+)?\d{4}-\d{2}-\d{2}$",
        ]
        risk_only_patterns = [
            r"^(masculino|femenino|hombre|mujer|varon|varón)(?:\s+a\s+\d+(?:[.,]\d+)?\s*km)?$",
            r"^a\s+\d+(?:[.,]\d+)?\s*km$",
            r"^\d+(?:[.,]\d+)?\s*km$",
        ]
        return any(re.match(p, t, re.IGNORECASE) for p in (time_patterns + date_patterns + risk_only_patterns))

    def _extraer_datos_riesgo(self, text: str) -> dict:
        """Extrae datos hablados para llenar el formulario de predicción IA."""
        t = text.lower()
        data = {}

        gen = re.search(r"\b(masculino|femenino|hombre|mujer|varon|varón)\b", t)
        if gen:
            raw = gen.group(1)
            data["gender"] = "masculino" if raw in ("masculino", "hombre", "varon", "varón") else "femenino"

        edad = re.search(r"(?:edad|tiene|de)\s*(\d{1,3})\s*(?:años|anos)?", t)
        if edad:
            data["patient_age"] = int(edad.group(1))

        prioridad = re.search(r"\b(normal|baja|media|alta|urgente)\b", t)
        if prioridad:
            pr = prioridad.group(1)
            data["priority"] = "media" if pr == "normal" else pr

        faltas = re.search(r"(?:faltas?|inasistencias?|no\s*show|previas?)\D*(\d{1,2})", t)
        if faltas:
            data["previous_no_show_count"] = int(faltas.group(1))

        dist = re.search(r"(?:distancia|vive|a)\D*(\d+(?:[.,]\d+)?)\s*km", t)
        if dist:
            data["distance_km"] = float(dist.group(1).replace(",", "."))

        espera = re.search(r"(?:espera|esperar|esperada|estimada)\D*(\d{1,3})", t)
        if espera:
            data["waiting_minutes_estimated"] = int(espera.group(1))

        return data

    def _estimate_waiting_time(self, doctor_id: int | None, shift: str) -> int:
        """Estima minutos de espera según turno (mañana=tranquilo, tarde=mayor espera)."""
        return 15 if shift == "manana" else 30

    def _compute_risk_features(self, paciente, doctor, scheduled_at, reason: str | None = None, distance_km: float | None = None) -> dict:
        features = {
            "patient_age": 30,
            "gender": "No especificado",
            "specialty": doctor.specialty if doctor else "Medicina General",
            "priority": self._infer_priority(reason),
            "appointment_shift": "manana",
            "previous_no_show_count": 0,
            "distance_km": distance_km if distance_km else 5.0,
            "days_until_appointment": 7,
            "waiting_minutes_estimated": 15,
        }
        origins = {
            "patient_age": "default",
            "gender": "default",
            "specialty": "real" if doctor else "default",
            "priority": "inferido",
            "appointment_shift": "default",
            "previous_no_show_count": "default",
            "distance_km": "default",
            "days_until_appointment": "default",
            "waiting_minutes_estimated": "default",
        }
        try:
            if paciente:
                if paciente.birth_date:
                    today = date.today()
                    edad = today.year - paciente.birth_date.year
                    if today.month < paciente.birth_date.month or (
                        today.month == paciente.birth_date.month
                        and today.day < paciente.birth_date.day
                    ):
                        edad -= 1
                    features["patient_age"] = edad
                    origins["patient_age"] = "real"
                if getattr(paciente, "gender", None):
                    features["gender"] = paciente.gender
                    origins["gender"] = "real"
                features["previous_no_show_count"] = self._count_previous_no_shows(paciente.id)
                origins["previous_no_show_count"] = "real"
            if hasattr(scheduled_at, "hour"):
                shift = "manana" if scheduled_at.hour < 12 else "tarde"
                features["appointment_shift"] = shift
                origins["appointment_shift"] = "real"
                features["waiting_minutes_estimated"] = self._estimate_waiting_time(
                    doctor.id if doctor else None, shift
                )
                origins["waiting_minutes_estimated"] = "real"
            if hasattr(scheduled_at, "date"):
                days_until = (scheduled_at.date() - date.today()).days
                features["days_until_appointment"] = max(days_until, 0)
                origins["days_until_appointment"] = "real"
            if distance_km is not None:
                features["distance_km"] = distance_km
                origins["distance_km"] = "real"
            features["priority"] = self._infer_priority(reason)
            origins["priority"] = "inferido"
        except Exception:
            pass
        features["_origins"] = origins
        return features

    def _predecir_riesgo(self, paciente, doctor, scheduled_at, reason, distance_km=None, gender_text="") -> dict | None:
        risk = self._get_risk_service()
        if risk is None:
            return None
        try:
            features = self._compute_risk_features(paciente, doctor, scheduled_at, reason, distance_km)
            if gender_text:
                features["gender"] = gender_text
            origins = features.pop("_origins", {})
            result = risk.predict_risk(**features)
            if result:
                result["feature_origins"] = origins
                result["feature_values"] = features
            return result
        except Exception:
            return None

    @staticmethod
    def _es_frase_generica(text: str) -> bool:
        """Retorna True si el texto es una frase genérica de intención, no un nombre."""
        generic_words = {
            "agendar", "cita", "médica", "medica", "médico", "medico",
            "doctor", "doctora", "dra", "dr", "lic", "especialidad",
            "especialista", "consulta", "revisión", "revision", "control",
            "emergencia", "urgencia", "programar", "reservar", "sacar",
            "quiero", "necesito", "puedo", "podría", "podrias",
            "registrar", "cancelar", "reprogramar", "mover", "cambiar",
            "información", "informacion", "info", "ayuda", "hola", "buenos",
            "buenas", "tardes", "dias", "días", "noches", "saludos",
        }
        words = set(text.lower().split())
        return bool(words & generic_words)

    def _extraer_nombre_simple(self, text: str) -> tuple[str, str]:
        """Si el texto son solo palabras alfabéticas (nombre), lo usa como nombre completo."""
        from .intent_detector import limpiar_nombre
        # Rechazar si contiene indicios de email
        if "@" in text or ".com" in text.lower() or ".pe" in text.lower():
            return ("", "")
        clean = re.sub(r"[^\w\sáéíóúñüäëöÁÉÍÓÚÑÜÄËÖ]", "", text).strip()
        words = [w for w in clean.split() if w.isalpha()]
        STOP_KW = {"dni", "telefono", "telefónico", "email", "correo", "fecha",
                   "nacimiento", "sexo", "masculino", "femenino", "mujer", "hombre",
                   "varon", "edad", "direccion", "numero", "cita", "crear", "nuevo",
                   "nueva", "para", "quiero"}
        if 1 <= len(words) <= 5 and not any(w.lower() in STOP_KW for w in words):
            return limpiar_nombre(clean)
        return ("", "")

    def collect_appointment(self, text: str, entities: dict, user_name: str = "") -> dict:
        """Flujo conversacional paso a paso para agendar cita.

        Regla crítica:
        - Primero se recogen datos y se calcula riesgo IA.
        - La cita NO se crea hasta que recepción diga: crear cita o confirmar cita.
        """
        nombre = user_name or "Usuario"
        clean = text.lower().strip()
        _patient_just_created = False

        # ── 0. DECISIÓN SOBRE CITA PENDIENTE DESPUÉS DE PREDICCIÓN IA ──
        draft = entities.get("_draft_appointment")
        if draft:
            quiere_confirmar = any(x in clean for x in ["confirmar cita", "generar ticket", "confirmar", "ticket"])
            quiere_crear = any(x in clean for x in ["crear cita", "guardar cita", "crear", "guardar"])
            quiere_llamar = any(x in clean for x in ["llamar paciente", "llamar"])
            quiere_cancelar = any(x in clean for x in ["cancelar", "no crear", "anular", "descartar"])

            if quiere_llamar:
                return {
                    "type": "success",
                    "action": "agendar_cita",
                    "target": "appointments",
                    "message": (
                        f"{nombre}, correcto. No se creó la cita. "
                        "Primero llama al paciente y luego puedes confirmar o cancelar la atención."
                    ),
                    "voice": "Correcto. No se creó la cita. Primero llama al paciente.",
                }

            if quiere_cancelar:
                return {
                    "type": "success",
                    "action": "agendar_cita",
                    "target": "appointments",
                    "message": f"{nombre}, cita descartada. No se creó ningún registro.",
                    "voice": "Cita descartada. No se creó ningún registro.",
                }

            if quiere_crear or quiere_confirmar:
                try:
                    payload = AppointmentCreate(
                        paciente_id=int(draft["patient_id"]),
                        medico_id=int(draft["doctor_id"]),
                        programada_en=datetime.fromisoformat(str(draft["scheduled_at"])).replace(tzinfo=UTC),
                        motivo=draft.get("reason") or "Consulta médica",
                    )

                    appointment = self.service.create_appointment(payload)

                    if quiere_confirmar:
                        ticket = self.service.confirm_appointment(appointment.id)
                        return {
                            "type": "success",
                            "action": "confirmar_cita",
                            "target": "appointments",
                            "message": (
                                f"Cita creada y confirmada correctamente.\n"
                                f"ID cita: #{appointment.id}\n"
                                f"Ticket médico: **{ticket.code}**\n"
                                "El paciente y el médico deben recibir la notificación correspondiente si el correo está configurado."
                            ),
                            "voice": "Cita creada, confirmada y ticket médico generado correctamente.",
                            "ticket": {
                                "id": ticket.id,
                                "appointment_id": ticket.appointment_id,
                                "code": ticket.code,
                                "is_confirmed": ticket.is_confirmed,
                            },
                        }

                    return {
                        "type": "success",
                        "action": "agendar_cita",
                        "target": "appointments",
                        "message": f"Cita creada correctamente. ID cita: #{appointment.id}. Aún no tiene ticket confirmado.",
                        "voice": "Cita creada correctamente. Aún no tiene ticket confirmado.",
                    }
                except Exception as e:
                    return {
                        "type": "error",
                        "action": "agendar_cita",
                        "message": f"{nombre}, no pude crear la cita pendiente: {str(e)}",
                        "voice": "No pude crear la cita pendiente. Revisa los datos o intenta nuevamente.",
                    }

            return {
                "type": "info",
                "action": "agendar_cita",
                "message": (
                    f"{nombre}, hay una cita pendiente después de la predicción IA. "
                    "Dime: **crear cita**, **confirmar cita**, **llamar paciente** o **cancelar**."
                ),
            }

        # ── 1. PACIENTE ────────────────────────────────────────
        _old_patient_id = entities.get("patient_id")
        paciente = None
        patient_id = entities.get("patient_id")
        if patient_id:
            try:
                paciente = self.service.repositorio_pacientes.obtener_por_id(patient_id)
            except Exception:
                pass
        if not paciente:
            try:
                # Buscar por DNI en pending primero
                pending = entities.get("_pending_patient", {})
                if pending.get("document_number"):
                    try:
                        paciente = self.patient_actions._buscar(pending["document_number"])
                        entities["patient_id"] = paciente.id
                    except NotFoundException:
                        pass
            except Exception:
                pass
        if not paciente:
            try:
                paciente = self.patient_actions._buscar(text, user_name=user_name)
                entities["patient_id"] = paciente.id
            except NotFoundException:
                pass

        # Si no hay paciente y la frase no contiene nombre/paciente,
        # preguntar por el paciente antes de crear uno nuevo.
        _has_patient_ctx = entities.get("_patient_step") or entities.get("_pending_patient", {}).get("first_name")
        if not paciente and not _has_patient_ctx:
            _name_hints = ["para", "paciente", "soy", "llamo", "nombre", "buscar",
                           "dni", "documento", "email", "correo"]
            clean_lower = text.lower().strip()
            has_name_hint = any(h in clean_lower.split() for h in _name_hints) or not self._es_frase_generica(clean_lower)
            if not has_name_hint and entities.get("_patient_step") is None:
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": f"{nombre}, ¿para qué **paciente** desea agendar la cita?",
                }

        # ── Si no se encontró paciente pero el texto parece un nombre,
        #     preguntar si desea crearlo antes de entrar a PHASE 1 ──
        _pending_creation = entities.get("_pending_creation")
        if not paciente and not _has_patient_ctx and not _pending_creation:
            candidate = extraer_datos_paciente(text)
            candidate_name = candidate.get("first_name", "").strip()
            if candidate_name and len(candidate_name) > 1:
                entities["_pending_creation"] = {
                    "name": candidate_name,
                    "text": text,
                }
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": (
                        f"{nombre}, no encontré al paciente **{candidate_name}**. "
                        "¿Desea crearlo? (Di **sí** para crearlo o **no** para intentar con otro nombre)"
                    ),
                }

        # Sí confirmó crear paciente → iniciar PHASE 1
        if _pending_creation:
            confirm = any(x in clean for x in ["si", "sí", "crear", "crearlo", "registrar", "nuevo", "dale", "ok", "claro", "adelante"])
            if not confirm:
                entities.pop("_pending_creation", None)
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": f"{nombre}, dígame el **nombre del paciente** para buscar o crear.",
                }
            # Pre-fill pending patient with the name from creation confirmation
            pending_text = _pending_creation.get("text", "")
            _pending_from_confirm = entities.setdefault("_pending_patient", {})
            if not _pending_from_confirm.get("first_name"):
                first, last = self._extraer_nombre_simple(pending_text)
                if first:
                    _pending_from_confirm["first_name"] = " ".join(filter(None, [first, last]))
            entities["_patient_step"] = "last_name"
            entities.pop("_pending_creation", None)
            return {
                "type": "info",
                "action": "agendar_cita",
                "message": f"{nombre}, los **apellidos** del paciente. Ej: 'Chávez Miranda'",
            }

        # ── PHASE 1: Collect patient data step by step ──────────
        if not paciente:
            # If we already sent prefill, wait for the user to submit the form
            if entities.get("_patient_step") == "done":
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": f"{nombre}, por favor completa y confirma el formulario del paciente para continuar con la cita.",
                }
            pending = entities.get("_pending_patient", {})
            step_atual = entities.get("_patient_step", "")

            # Siempre limpiar nombres para que se pregunten por separado
            if not step_atual:
                pending.pop("first_name", None)
                pending.pop("last_name", None)

            datos = extraer_datos_paciente(text)

            # Detect correction intent: "corrige X", "no, el X es", "X mal", etc.
            correction_match = re.match(
                r"(?:(?:no|error)\s*[,\s]*)?"
                r"(?:(?:el|la)\s+)?"
                r"(?:(?:corrige|corregir|cambiar|cambio|correcci[oó]n)\s+(?:el|la\s+)?)?"
                r"\s*"
                r"(dni|documento|nombres|nombre|apellidos|apellido|"
                r"email|correo|telefono|teléfono|tlf|celular|fecha|edad)"
                r"(?:\s+(?:es|deber[ií]a\s+ser|ser[ií]a|a\s+)?)"
                r"(.+)$",
                clean, re.IGNORECASE,
            )
            if correction_match:
                field_key = correction_match.group(1).lower()
                field_value = correction_match.group(2).strip()
                if field_key in ("dni", "documento"):
                    nums = re.sub(r"\D", "", field_value)
                    if len(nums) >= 7:
                        pending["document_number"] = nums
                elif field_key in ("nombres", "nombre"):
                    pending.pop("first_name", None)
                    pending.pop("last_name", None)
                elif field_key in ("apellidos", "apellido"):
                    pending.pop("last_name", None)
                elif field_key in ("email", "correo"):
                    ed = extraer_datos_paciente(field_value)
                    if ed.get("email"):
                        pending["email"] = ed["email"]
                elif field_key in ("telefono", "teléfono", "tlf", "celular"):
                    nums = re.sub(r"\D", "", field_value)
                    if len(nums) >= 7:
                        pending["phone"] = nums[:9]
                elif field_key in ("fecha", "edad"):
                    ed = extraer_datos_paciente(field_value)
                    if ed.get("birth_date"):
                        pending["birth_date"] = ed["birth_date"]

            # Merge extracted data (sin nombres, se manejan abajo por paso)
            if datos.get("document_number") and len(datos["document_number"]) >= 7:
                pending["document_number"] = datos["document_number"]
            if datos.get("phone"):
                pending["phone"] = datos["phone"]
            if datos.get("email"):
                pending["email"] = datos["email"]
            if datos.get("birth_date"):
                pending["birth_date"] = datos["birth_date"]
            if datos.get("gender"):
                pending["gender"] = datos["gender"]

            # Manejo de nombres según el paso actual
            if step_atual == "first_name":
                if datos.get("first_name"):
                    pending["first_name"] = datos["first_name"]
                elif not pending.get("first_name"):
                    first, last = self._extraer_nombre_simple(text)
                    if first:
                        pending["first_name"] = " ".join(filter(None, [first, last]))
            elif step_atual == "last_name":
                if datos.get("last_name"):
                    pending["last_name"] = datos["last_name"]
                elif not pending.get("last_name"):
                    if re.match(r"^[\wáéíóúñü\s]+$", text.strip(), re.IGNORECASE):
                        pending["last_name"] = text.strip()
            else:
                # Sin paso activo de nombres: extraer todo como first_name
                if not pending.get("first_name"):
                    first, last = self._extraer_nombre_simple(text)
                    if first:
                        pending["first_name"] = " ".join(filter(None, [first, last]))

            # Build missing list in order
            FIELD_QUESTIONS = []
            if not pending.get("first_name"):
                FIELD_QUESTIONS.append(("first_name", "los **nombres** del paciente. Ej: 'Michael Jeremías'"))
            if not pending.get("last_name"):
                FIELD_QUESTIONS.append(("last_name", "los **apellidos** del paciente. Ej: 'Chávez Miranda'"))
            if not pending.get("document_number"):
                FIELD_QUESTIONS.append(("dni", "el **número de DNI**. Ej: '12345678'"))
            if not pending.get("phone"):
                FIELD_QUESTIONS.append(("phone", "el **número de teléfono**. Ej: '987654321'"))
            if not pending.get("email"):
                FIELD_QUESTIONS.append(("email", "el **correo electrónico**. Ej: 'rocio@correo.pe'"))
            if not pending.get("birth_date"):
                FIELD_QUESTIONS.append(("birth", "la **fecha de nacimiento**. Ej: '6 de noviembre del 2006'"))
            if not pending.get("gender"):
                FIELD_QUESTIONS.append(("gender", "el **sexo** (masculino o femenino)"))

            if FIELD_QUESTIONS:
                step_name, question = FIELD_QUESTIONS[0]
                entities["_pending_patient"] = pending
                entities["_patient_step"] = step_name
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": f"{nombre}, {question}",
                }

            # All 6 fields collected → crear paciente directo
            from app.schemas.patient import PacienteCrear
            import datetime as _dt
            try:
                new_patient = self.service.repositorio_pacientes.crear(PacienteCrear(
                    nombres=pending["first_name"].title(),
                    apellidos=pending["last_name"].title(),
                    numero_documento=pending["document_number"],
                    correo=pending.get("email") or f"{pending['first_name']}.{pending['last_name']}@correo.temporal",
                    telefono=pending.get("phone") or "999999999",
                    fecha_nacimiento=(
                        _dt.datetime.strptime(pending["birth_date"], "%Y-%m-%d").date()
                        if pending.get("birth_date")
                        else _dt.date(2000, 1, 1)
                    ),
                    genero=pending.get("gender"),
                ))
                entities["patient_id"] = new_patient.id
                entities.pop("_pending_patient", None)
                entities.pop("_patient_step", None)
                entities.pop("date", None)
                entities.pop("time", None)
                paciente = new_patient
                _patient_just_created = True
            except Exception as e:
                return {
                    "type": "error",
                    "action": "agendar_cita",
                    "message": f"{nombre}, no pude crear el paciente: {str(e)}",
                }
        # ── Confirmar retomar cita después de crear paciente ──
        if _patient_just_created:
            entities["_continue_appointment"] = True
            return {
                "type": "info",
                "action": "agendar_cita",
                "message": (
                    f"{nombre}, paciente **{paciente.first_name} {paciente.last_name}** creado correctamente.\n"
                    "¿Desea retomar la cita médica para este paciente? (Di **sí** para continuar)"
                ),
            }

        _cont = entities.pop("_continue_appointment", None)
        if _cont:
            confirm_cont = any(x in clean for x in ["si", "sí", "continuar", "retomar", "dale", "ok", "claro", "adelante"])
            if not confirm_cont:
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": f"{nombre}, cita cancelada. Puede agendar una nueva cuando desee.",
                    "voice": "Cita cancelada.",
                }

        _pac_created = f"Paciente {paciente.first_name} {paciente.last_name} creado. " if _patient_just_created else ""
        doctor_id_ctx = entities.get("doctor_id")
        doctor = None
        if doctor_id_ctx:
            try:
                doctor = self.service.repositorio_medicos.obtener_por_id(doctor_id_ctx)
            except Exception:
                pass
        _patient_found_now = entities.get("patient_id") != _old_patient_id
        _has_explicit_doctor = bool(re.search(r'\b(?:dr|doctor|doctora|dra|médico|medico)\.?\s', text.lower()))
        if not doctor and (not _patient_found_now or _has_explicit_doctor):
            try:
                doctor = self.doctor_actions._buscar(text, entities.get("specialty"))
            except NotFoundException:
                pass

        if doctor:
            entities["doctor_id"] = doctor.id
        else:
            # Check if a doctor name was provided but not found → create inline
            doc_datos = extraer_datos_medico(text)
            doc_fn = doc_datos.get("first_name", "")
            doc_ln = doc_datos.get("last_name", "")
            doc_spec = doc_datos.get("specialty") or entities.get("specialty")
            if doc_fn and doc_ln and doc_spec:
                from app.schemas.doctor import DoctorCreate
                try:
                    new_doc = self.service.repositorio_medicos.crear(DoctorCreate(
                        nombres=doc_fn.title(),
                        apellidos=doc_ln.title(),
                        especialidad=doc_spec,
                        correo=doc_datos.get("email") or f"{doc_fn}.{doc_ln}@hospital.pe",
                    ))
                    doctor = new_doc
                    entities["doctor_id"] = doctor.id
                except Exception as e:
                    return {
                        "type": "info",
                        "action": "agendar_cita",
                        "message": f"{nombre}, el médico {doc_fn} {doc_ln} no está registrado y no pude crearlo: {str(e)}. ¿Puedes intentar con otro médico?",
                    }
            elif doc_fn and doc_ln:
                msg = f"{_pac_created}el médico **{doc_fn} {doc_ln}** no está registrado. ¿Cuál es su especialidad? (Ej: 'cardiología')"
                return {"type": "info", "action": "agendar_cita", "message": f"{nombre}, {msg}"}
            elif entities.get("specialty"):
                msg = f"{_pac_created}no encontré un médico de **{entities['specialty']}** disponible. ¿Puedes darme el nombre completo del médico?"
                return {"type": "info", "action": "agendar_cita", "message": f"{nombre}, {msg}"}
            else:
                msg = f"{_pac_created}¿qué **médico** o **especialidad** deseas? Ejemplo: 'Dr. Pedro Ambrosio' o 'cardiología'"
                return {"type": "info", "action": "agendar_cita", "message": f"{nombre}, {msg}"}

        # ── 3. FECHA ────────────────────────────────────────────
        scheduled_at = entities.get("date")
        if not scheduled_at:
            return {
                "type": "info",
                "action": "agendar_cita",
                "message": (
                    f"{_pac_created}{nombre}, ¿para qué **fecha** deseas la cita con "
                    f"el Dr. {doctor.first_name} {doctor.last_name}? "
                    f"Ejemplo: 'mañana', '29 de mayo' o '15 de junio'"
                ),
            }
        try:
            datetime.strptime(scheduled_at, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            entities.pop("date", None)
            return {
                "type": "info",
                "action": "agendar_cita",
                "message": (
                    f"{nombre}, la fecha **{scheduled_at}** no es válida "
                    f"(ej: 31 de junio no existe). "
                    f"¿Puedes repetir la fecha?"
                ),
            }

        # ── 4. HORA ─────────────────────────────────────────────
        hora = entities.get("time")
        if not hora:
            return {
                "type": "info",
                "action": "agendar_cita",
                "message": (
                    f"{nombre}, ¿a qué **hora** deseas la cita el "
                    f"{scheduled_at}? "
                    f"El Dr. {doctor.first_name} {doctor.last_name} atiende de 8:00 a 17:00. "
                    f"Ejemplo: '10:30'"
                ),
            }

        # ── 5. MOTIVO ───────────────────────────────────────────
        reason = entities.get("reason")
        if not reason:
            candidate = text.strip().rstrip(".,;")
            if len(candidate) > 3 and not self._is_only_time_or_date(candidate):
                reason = candidate
                entities["reason"] = reason
            else:
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": f"{nombre}, ¿cuál es el **motivo real de la consulta**? Ejemplo: control cardiológico, dolor de pecho, control general.",
                }

        # ── 6. DATOS COMPLETOS PARA PREDICCIÓN DE RIESGO ─────────
        scheduled_dt = datetime.strptime(f"{scheduled_at} {hora}:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        risk_pending = dict(entities.get("_pending_risk", {}))
        risk_pending.update(self._extraer_datos_riesgo(text))

        # Datos auto-calculables del paciente y la cita
        if getattr(paciente, "birth_date", None):
            today = date.today()
            age = today.year - paciente.birth_date.year - (
                (today.month, today.day) < (paciente.birth_date.month, paciente.birth_date.day)
            )
            risk_pending["patient_age"] = age
        if getattr(paciente, "gender", None):
            risk_pending["gender"] = paciente.gender
        if doctor and doctor.specialty:
            risk_pending["specialty"] = doctor.specialty
        else:
            risk_pending.setdefault("specialty", "Medicina General")
        risk_pending["appointment_shift"] = "manana" if scheduled_dt.hour < 12 else ("tarde" if scheduled_dt.hour < 18 else "noche")
        risk_pending["days_until_appointment"] = max((scheduled_dt.date() - date.today()).days, 0)
        risk_pending.setdefault("priority", self._infer_priority(reason))

        missing_risk = []
        if "previous_no_show_count" not in risk_pending:
            missing_risk.append("faltas previas")
        if "distance_km" not in risk_pending:
            missing_risk.append("distancia km")
        if "waiting_minutes_estimated" not in risk_pending:
            missing_risk.append("espera estimada")

        if missing_risk:
            entities["_pending_risk"] = risk_pending
            return {
                "type": "info",
                "action": "agendar_cita",
                "message": (
                    f"{nombre}, antes de crear la cita necesito unos datos para la **Predicción IA de Riesgo de Inasistencia**.\n"
                    f"Me faltan: {', '.join(missing_risk)}.\n"
                    "Puedes decirlos así: 'faltas previas 0, distancia 15 km, espera 15 minutos'."
                ),
            }

        distancia = float(risk_pending["distance_km"])
        gender_text = risk_pending.get("gender", "")

        # ── 7. TODOS LOS DATOS — PRIMERO PREDICCIÓN, NO CREAR CITA ────────────

        citas_del_dia = self.service.repositorio_citas.obtener_citas_medico_en_fecha(
            doctor.id, scheduled_dt
        )

        for c in citas_del_dia:
            if abs((c.scheduled_at - scheduled_dt).total_seconds()) < 3600:
                return {
                    "type": "info",
                    "action": "agendar_cita",
                    "message": (
                        f"El Dr. {doctor.first_name} {doctor.last_name} ya tiene una cita "
                        f"a las {c.scheduled_at.strftime('%H:%M')} de ese día. "
                        f"¿Deseas otra hora u otro día?"
                    ),
                }

        risk_data = {
            "patient_age": int(risk_pending["patient_age"]),
            "gender": risk_pending["gender"],
            "specialty": risk_pending["specialty"],
            "priority": risk_pending["priority"],
            "appointment_shift": risk_pending["appointment_shift"],
            "previous_no_show_count": int(risk_pending["previous_no_show_count"]),
            "distance_km": float(risk_pending["distance_km"]),
            "days_until_appointment": int(risk_pending["days_until_appointment"]),
            "waiting_minutes_estimated": int(risk_pending["waiting_minutes_estimated"]),
        }

        riesgo = None
        risk = self._get_risk_service()
        if risk is not None:
            try:
                riesgo = risk.predict_risk(**risk_data)
                riesgo["feature_values"] = risk_data
            except Exception as e:
                riesgo = {"risk_level": "desconocido", "confidence": 0.0, "model": "error", "error": str(e)}

        riesgo_msg = "No se pudo calcular el riesgo IA."
        if riesgo and riesgo.get("model") != "not_loaded":
            nivel = riesgo.get("risk_level", "desconocido").upper()
            confianza = round(float(riesgo.get("confidence", 0)) * 100, 1)
            riesgo_msg = (
                f"Predicción IA de inasistencia:\n"
                f"Riesgo: {nivel}\n"
                f"Confianza: {confianza}%\n"
                f"Modelo: {riesgo.get('model', 'desconocido')}"
            )
        elif riesgo and riesgo.get("model") == "not_loaded":
            riesgo_msg = "No se pudo calcular el riesgo IA porque el modelo no está cargado."

        prefill = {
            "patient_id": paciente.id,
            "doctor_id": doctor.id,
            "scheduled_at": scheduled_dt.strftime("%Y-%m-%dT%H:%M"),
            "reason": reason,
        }

        entities["_draft_appointment"] = prefill
        entities["risk_data"] = risk_data

        return {
            "type": "prefill",
            "action": "agendar_cita",
            "target": "appointments",
            "prefill": prefill,
            "risk_data": risk_data,
            "risk_result": riesgo,
            "message": (
                f"{nombre}, ya tengo los datos de la cita, pero aún NO la he creado.\n\n"
                f"Paciente: {paciente.first_name} {paciente.last_name}\n"
                f"Médico: {doctor.first_name} {doctor.last_name} ({doctor.specialty})\n"
                f"Fecha: {scheduled_dt.strftime('%d/%m/%Y %H:%M')}\n"
                f"Motivo: {reason}\n\n"
                f"{riesgo_msg}\n\n"
                f"Decisión requerida:\n"
                f"- Di **crear cita** para guardarla sin ticket.\n"
                f"- Di **confirmar cita** para crearla y generar ticket.\n"
                f"- Di **llamar paciente** si deseas llamar antes.\n"
                f"- Di **cancelar** para no crear la cita."
            ),
            "voice": (
                f"{nombre}, ya tengo los datos y la predicción de riesgo. "
                f"Aún no crearé la cita. Dime: crear cita, confirmar cita, llamar paciente o cancelar."
            ),
        }

    def cancelar(self, text: str, user_name: str = "") -> dict:
        try:
            paciente = self.patient_actions._buscar(text, user_name=user_name)
            citas = self.service.list_appointments(limit=50)
            pending = [
                a for a in citas
                if a.patient_id == paciente.id and a.status in ("pending", "confirmed", "PENDING", "CONFIRMED")
            ]
            if not pending:
                return {
                    "type": "info",
                    "message": f"{paciente.first_name} {paciente.last_name} no tiene citas pendientes para cancelar.",
                    "action": "cancelar_cita",
                }
            appt = pending[0]
            self.service.cancel_appointment(appt.id)
            return {
                "type": "success",
                "message": f"Cita #{appt.id} cancelada exitosamente. Paciente: {paciente.first_name} {paciente.last_name}.",
                "action": "cancelar_cita",
                "appointment_id": appt.id,
            }
        except (NotFoundException, ConflictException) as e:
            msg = str(e.detail if hasattr(e, "detail") else str(e))
            if "No se encontró el paciente" in msg:
                msg = "Para cancelar una cita, dime el nombre del paciente o su DNI. Por ejemplo: 'Juan Perez' o 'DNI 12345678'"
            return {"type": "info", "message": msg, "action": "cancelar_cita"}
        except Exception as e:
            return {"type": "error", "message": f"Error al cancelar: {str(e)}", "action": "cancelar_cita"}

    def consultar(self, text: str, user_name: str = "") -> dict:
        try:
            paciente = self.patient_actions._buscar(text, user_name=user_name)
            citas = self.service.list_appointments(limit=50)
            paciente_citas = [
                a for a in citas
                if a.patient_id == paciente.id
            ]
            if not paciente_citas:
                return {
                    "type": "info",
                    "message": f"{paciente.first_name} {paciente.last_name} no tiene citas registradas.",
                    "action": "consultar_cita",
                }
            lines = [f"Últimas citas de {paciente.first_name} {paciente.last_name}:"]
            for a in paciente_citas[:10]:
                doc = a.doctor
                doc_name = f"{doc.first_name} {doc.last_name}" if doc else "N/A"
                fecha = a.scheduled_at.strftime("%d/%m/%Y %H:%M") if hasattr(a.scheduled_at, "strftime") else str(a.scheduled_at)
                lines.append(f"  #{a.id} - {doc_name} - {fecha} - {fmt_estado(a.status)}")
            return {"type": "success", "message": "\n".join(lines), "action": "consultar_cita", "target": "appointments"}
        except NotFoundException:
            citas = self.service.list_appointments(limit=10)
            if citas:
                lines = ["Citas recientes del hospital:"]
                for a in citas[:10]:
                    pac = a.patient
                    pac_name = f"{pac.first_name} {pac.last_name}" if pac else "N/A"
                    doc = a.doctor
                    doc_name = f"{doc.first_name} {doc.last_name}" if doc else "N/A"
                    fecha = a.scheduled_at.strftime("%d/%m/%Y %H:%M") if hasattr(a.scheduled_at, "strftime") else str(a.scheduled_at)
                    lines.append(f"  #{a.id} {pac_name} con {doc_name} - {fecha} - {fmt_estado(a.status)}")
                return {"type": "success", "message": "\n".join(lines), "action": "consultar_cita", "target": "appointments"}
            return {"type": "info", "message": "No hay citas registradas en el sistema. ¿Quieres agendar una?", "action": "consultar_cita"}
        except Exception as e:
            return {"type": "error", "message": f"Error: {str(e)}", "action": "consultar_cita"}

    def eliminar(self, text: str, user_name: str = "") -> dict:
        try:
            paciente = self.patient_actions._buscar(text, user_name=user_name)
            citas = self.service.list_appointments(limit=50)
            pendientes = [
                a for a in citas
                if a.patient_id == paciente.id and a.status in ("pending", "confirmed", "PENDING", "CONFIRMED")
            ]
            if not pendientes:
                return {
                    "type": "info",
                    "message": f"{paciente.first_name} {paciente.last_name} no tiene citas pendientes para eliminar.",
                    "action": "eliminar_cita",
                }
            appt = pendientes[0]
            self.service.delete_appointment(appt.id)
            return {
                "type": "success",
                "message": f"Cita #{appt.id} eliminada permanentemente. Paciente: {paciente.first_name} {paciente.last_name}.",
                "action": "eliminar_cita",
                "appointment_id": appt.id,
            }
        except (NotFoundException, ConflictException) as e:
            msg = str(e.detail if hasattr(e, "detail") else str(e))
            return {"type": "error", "message": msg, "action": "eliminar_cita"}
        except Exception as e:
            return {"type": "error", "message": f"Error al eliminar cita: {str(e)}", "action": "eliminar_cita"}

    def listar(self, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        return {
            "type": "success",
            "message": f"{nombre}, te he llevado a la sección de citas.\n¿Deseas **agendar**, **cancelar**, **reprogramar** o **eliminar** alguna cita?",
            "action": "ver_citas",
            "target": "appointments",
        }

    def confirm(self, text: str, entities: dict, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        appointment_id = entities.get("appointment_id")
        if not appointment_id:
            citas = self.service.list_appointments(limit=5)
            pendientes = [c for c in citas if c.status in ("pending", "PENDING")]
            if not pendientes:
                return {
                    "type": "info",
                    "message": f"{nombre}, no hay citas pendientes por confirmar.",
                    "action": "confirmar_cita",
                }
            appointment_id = pendientes[0].id
        try:
            ticket = self.service.confirm_appointment(appointment_id)
            return {
                "type": "success",
                "action": "confirmar_cita",
                "message": (
                    f"Cita #{appointment_id} confirmada y ticket generado.\n"
                    f"Código de ticket: **{ticket.code}**\n"
                    f"Presenta este código en recepción el día de tu cita."
                ),
                "voice": f"Cita confirmada. Tu código de ticket es {ticket.code}. Preséntalo en recepción.",
                "ticket": {
                    "id": ticket.id,
                    "appointment_id": ticket.appointment_id,
                    "code": ticket.code,
                    "is_confirmed": ticket.is_confirmed,
                    "emitido_en": ticket.emitido_en.isoformat() if ticket.emitido_en else None,
                },
                "target": "appointments",
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"{nombre}, error al confirmar la cita: {str(e)}",
                "action": "confirmar_cita",
            }

    def reprogramar(self, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        return {
            "type": "info",
            "message": f"{nombre}, para reprogramar una cita necesito que me digas:\n- Nombre del paciente\n- Nueva fecha deseada\n\nEj: 'reprogramar cita de María López para el 15 de junio'",
            "action": "reprogramar_cita",
        }
