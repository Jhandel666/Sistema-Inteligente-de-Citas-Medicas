from __future__ import annotations

import re

from app.services.assistant.intent_detector import (
    _normalize,
    detect_intent_by_rules,
    extract_entities,
    detectar_navegacion,
    nombre_pagina,
)
from app.services.assistant.patient_actions import PatientActions
from app.services.assistant.doctor_actions import DoctorActions
from app.services.assistant.appointment_actions import AppointmentActions
from app.services.assistant.risk_actions import collect_risk_data
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.services.appointment_service import AppointmentService


_INTENCIONES_UTIL = {
    "agendar_cita", "cancelar_cita", "consultar_cita", "reprogramar_cita",
    "consultar_doctor", "resultados_lab", "queja_reclamo",
    "crear_medico", "crear_paciente",
    "eliminar_medico", "eliminar_paciente", "eliminar_cita",
    "ver_pacientes", "ver_medicos", "ver_citas",
    "predecir_riesgo", "confirmar_cita",
}


class AssistantService:
    def __init__(
        self,
        patient_service: PatientService,
        doctor_service: DoctorService,
        appointment_service: AppointmentService,
    ) -> None:
        self.patient_actions = PatientActions(patient_service)
        self.doctor_actions = DoctorActions(doctor_service)
        self.appointment_actions = AppointmentActions(
            appointment_service,
            self.patient_actions,
            self.doctor_actions,
        )
        self._intent_service = None

    def process_message(self, text: str, user_name: str = "", history: list | None = None, context: dict | None = None) -> dict:
        clean = _normalize(text)
        history = history or []
        context = context or {}

        despedidas = ["gracias la ia", "adios", "chau", "hasta luego", "nos vemos"]
        if any(d in clean for d in despedidas) or clean.strip() in ["gracias", "muchas gracias"]:
            nombre = user_name or "Usuario"
            return {
                "type": "farewell",
                "message": f"¡De nada {nombre}! Estoy aquí para ayudarte cuando me necesites. Cuídate.",
                "intent": "despedida",
                "confidence": 1.0,
            }

        saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "oye la ia"]
        if any(s in clean for s in saludos) and not any(
            k in clean for k in ["agendar", "cancelar", "cita", "medico", "doctor", "emergencia"]
        ):
            nombre = user_name or "Usuario"
            return {
                "type": "greeting",
                "message": f"¡Hola {nombre}! Soy **La IA**, tu asistente inteligente del Hospital de Pichanaki. ¿En qué puedo ayudarte?\n\nPuedes pedirme: *agendar cita* • *consultar médico* • *información* • *emergencia*",
                "intent": "saludo",
                "confidence": 1.0,
            }

        # ── Cambio de tono de voz ──
        voz_m = re.search(r"(?:cambia|pon|activa|quiero)\s+.*(?:voz|tono).*(?:mujer|femenina|femenino)", clean)
        voz_f = re.search(r"(?:cambia|pon|activa|quiero)\s+.*(?:voz|tono).*(?:hombre|varon|masculina|masculino)", clean)
        if voz_m or voz_f:
            gender = "female" if voz_m else "male"
            label = "femenina" if voz_m else "masculina"
            name = user_name or "Usuario"
            return {
                "type": "voice_change",
                "message": f"¡Claro {name}! Cambiando la voz a **{label}**.",
                "voice": gender,
            }

        rule_intent = detect_intent_by_rules(clean)
        entities = extract_entities(clean)

        # ── Memoria conversacional: reusar intent + entidades pendientes ──
        stored_ctx = context.get("pending", {})
        has_pending = (
            stored_ctx.get("intent") and stored_ctx.get("intent") != "desconocido"
        )

        # Si existe una cita pendiente después de la predicción IA, las palabras
        # "crear", "confirmar", "llamar" o "cancelar" deben resolver ESA cita
        # y no iniciar otro flujo general.
        stored_entities = stored_ctx.get("entities", {}) if has_pending else {}
        has_draft_appointment = (
            has_pending
            and stored_ctx.get("intent") == "agendar_cita"
            and bool(stored_entities.get("_draft_appointment"))
        )
        is_draft_decision = has_draft_appointment and any(
            kw in clean
            for kw in (
                "crear cita", "guardar cita", "confirmar cita", "generar ticket",
                "llamar paciente", "llamar", "cancelar", "no crear", "anular",
            )
        )

        if is_draft_decision:
            rule_intent = "agendar_cita"
            entities = dict(stored_entities)
            entities.update({"_decision_text": text})

        # Si hay un flujo pendiente, sus respuestas deben ir al recolector del flujo,
        # no al detector general de intención. Solo se permite salir/reiniciar.
        # Si el texto contiene palabras de nueva petición, se trata como comando nuevo.
        _PETITION_KWS = [
            "agendar", "cancelar", "emergencia",
            "horario", "informacion", "resultados", "queja", "reclamo",
            "llevame", "navegar", "crear", "nuevo", "nueva",
            "ver", "mostrar", "listar", "lista",
            "gracias", "hola", "adios", "buenos",
            "eliminar", "borrar", "actualizar", "editar",
            "predecir", "riesgo", "prediccion",
        ]
        # Exclusiones contextuales para no romper flujos activos
        if not (has_pending and stored_ctx["intent"] == "predecir_riesgo"):
            _PETITION_KWS.append("cita")
        # "medico"/"doctor" no debe romper el flujo de agendar cita
        if not (has_pending and stored_ctx["intent"] in ("agendar_cita", "reprogramar_cita")):
            _PETITION_KWS.extend(["medico", "doctor"])

        tiene_nueva_peticion = any(kw in clean for kw in _PETITION_KWS)

        # Cuando hay un paciente pendiente y el usuario confirma con "sí" o "sí crear",
        # no tratarlo como nueva petición, sino como continuación del flujo.
        if has_pending and stored_ctx.get("entities", {}).get("_pending_patient"):
            if any(si in clean for si in ("si", "sí", "si crear", "sí crear", "dale", "ok", "vamos", "adelante", "claro", "confirmo")):
                tiene_nueva_peticion = False

        explicit_exit = any(k in clean for k in ("cancelar flujo", "reiniciar flujo", "salir del flujo", "olvidar flujo"))
        force_pending_flow = has_pending and not explicit_exit and not is_draft_decision and not tiene_nueva_peticion
        # Durante el flujo de riesgo, ignorar reglas activadas por "citas"
        rule_intent_ctx = rule_intent
        if has_pending and stored_ctx["intent"] == "predecir_riesgo":
            if rule_intent in ("consultar_cita", "ver_citas"):
                rule_intent_ctx = None
        # Durante flujo de paciente/cita, ignorar reglas activadas por palabras de datos de paciente
        if has_pending and stored_ctx["intent"] in ("crear_paciente", "agendar_cita"):
            if rule_intent in ("informacion_servicios",):
                rule_intent_ctx = None
        es_respuesta_paciente = (
            not tiene_nueva_peticion
            and 1 <= len(clean.split()) <= 10
            and not rule_intent_ctx
        )

        es_continuacion_flujo = False
        if has_pending and stored_ctx.get("intent") == "agendar_cita":
            comandos_nuevos = [
                "crear paciente", "crear medico", "crear médico",
                "ver pacientes", "ver medicos", "ver médicos", "ver citas",
                "eliminar paciente", "eliminar medico", "eliminar médico",
                "emergencia", "salir", "reiniciar",
            ]
            es_continuacion_flujo = not any(cmd in clean for cmd in comandos_nuevos)

        if is_draft_decision or force_pending_flow or (has_pending and (es_respuesta_paciente or es_continuacion_flujo) and not tiene_nueva_peticion):
            intent = stored_ctx["intent"]
            confidence = 0.75
            stored = dict(stored_ctx.get("entities", {}))
            stored.update({k: v for k, v in entities.items() if v})
            entities = stored
        else:
            # ── Sin contexto pendiente → detectar con reglas o ML ──
            if rule_intent:
                intent = rule_intent
                confidence = 0.80
            else:
                if self._intent_service is None:
                    from app.ml.inference.intent_service import MedicalIntentService
                    self._intent_service = MedicalIntentService()
                intent_result = self._intent_service.predict_intent(clean)
                intent = intent_result["intent"]
                confidence = intent_result["confidence"]

                if intent == "desconocido":
                    nav_target = detectar_navegacion(clean)
                    if nav_target:
                        intent = "navegar"
                        confidence = 0.80

            if not rule_intent and confidence < 0.60:
                nombre = user_name or "Usuario"
                return {
                    "type": "clarification",
                    "message": f"{nombre}, ¿podrías repetir con más detalle? No entendí bien tu solicitud.",
                    "intent": intent,
                    "confidence": confidence,
                }

            # ── Respuesta sin contexto pendiente → reusar del historial ──
            if es_respuesta_paciente and not tiene_nueva_peticion:
                last_intent = self._ultima_intencion_util(history)
                if last_intent:
                    intent = last_intent
                    confidence = 0.80

        action_map = {
            "agendar_cita": self._agendar,
            "cancelar_cita": self._cancelar,
            "consultar_cita": self._consultar,
            "reprogramar_cita": self._reprogramar,
            "consultar_doctor": self._consultar_doctor,
            "emergencia": self._emergencia,
            "informacion_servicios": self._informacion,
            "resultados_lab": self._resultados,
            "queja_reclamo": self._queja,
            "navegar": self._navegar,
            "crear_medico": self._crear_medico,
            "crear_paciente": self._crear_paciente,
            "eliminar_medico": self._eliminar_medico,
            "eliminar_paciente": self._eliminar_paciente,
            "eliminar_cita": self._eliminar_cita,
            "ver_pacientes": self._ver_pacientes,
            "ver_medicos": self._ver_medicos,
            "ver_citas": self._ver_citas,
            "predecir_riesgo": self._predecir_riesgo,
            "confirmar_cita": self._confirmar_cita,
        }

        # Preservar datos temporales del contexto solo si NO es una nueva petición
        if not tiene_nueva_peticion:
            for _key in ("_pending_patient", "_patient_step", "_pending_creation", "_continue_appointment", "_draft_appointment", "risk_data", "_original_text"):
                if has_pending and _key in stored_ctx.get("entities", {}):
                    if _key not in entities:
                        entities[_key] = stored_ctx["entities"][_key]

        handler = action_map.get(intent, self._default_handler)
        result = handler(text, entities, intent, confidence, user_name=user_name, history=history)

        # Encadenar creacion de paciente con agendacion de cita pendiente
        if result.get("type") == "prefill" and result.get("action") in ("crear_paciente", "crear_medico"):
            if has_pending and stored_ctx.get("intent") == "agendar_cita":
                original = stored_ctx.get("entities", {}).get("_original_text", stored_ctx.get("text", "") or text)
                result["chain"] = {"action": "agendar_cita", "text": original}

        # Almacenar contexto pendiente si la acción no se completó
        if result.get("type") in ("info", "prefill") and result.get("action") in _INTENCIONES_UTIL:
            pending_intent = result.get("action", intent)
            ctx_entities = dict(entities)

            if result.get("type") == "prefill" and result.get("prefill"):
                if result.get("action") == "agendar_cita":
                    ctx_entities["_draft_appointment"] = result["prefill"]
                    ctx_entities["risk_data"] = result.get("risk_data")
                    ctx_entities["risk_result"] = result.get("risk_result")
                elif result.get("action") == "crear_paciente":
                    ctx_entities["_pending_patient"] = result["prefill"]
                elif result.get("action") == "crear_medico":
                    ctx_entities["_pending_doctor"] = result["prefill"]

            # Preservar el texto original que disparó la intención pendiente
            if "_original_text" not in ctx_entities:
                if has_pending and stored_ctx.get("entities", {}).get("_original_text"):
                    ctx_entities["_original_text"] = stored_ctx["entities"]["_original_text"]
                elif not has_pending:
                    ctx_entities["_original_text"] = text

            result["context"] = {
                "pending": {
                    "intent": pending_intent,
                    "entities": ctx_entities,
                    "text": text,
                }
            }
        elif result.get("type") in ("success", "error", "farewell"):
            result["context"] = {"pending": {}}

        # Preguntar siguiente paso en acciones exitosas (si no hay follow-up propio)
        if result.get("type") == "success" and not result.get("message", "").endswith("?"):
            result["message"] += "\n\n¿Necesitas algo más?"

        return result

    # ─── Delegación a action classes ──────────────────────────

    def _agendar(self, text, entities, intent, confidence, user_name="", history=None):
        import sys
        print(f"[DEBUG _agendar] text={text!r} intent={intent!r}", file=sys.stderr)
        result = self.appointment_actions.collect_appointment(text, entities, user_name=user_name)
        print(f"[DEBUG _agendar] result action={result.get('action')!r} type={result.get('type')!r}", file=sys.stderr)
        return result

    def _cancelar(self, text, entities, intent, confidence, user_name="", history=None):
        return self.appointment_actions.cancelar(text, user_name=user_name)

    def _consultar(self, text, entities, intent, confidence, user_name="", history=None):
        return self.appointment_actions.consultar(text, user_name=user_name)

    def _reprogramar(self, text, entities, intent, confidence, user_name="", history=None):
        nombre = user_name or "Usuario"
        return {
            "type": "info",
            "message": f"{nombre}, para reprogramar una cita dime los detalles: paciente, fecha actual y nueva fecha deseada.",
            "action": "reprogramar_cita",
        }

    def _eliminar_cita(self, text, entities, intent, confidence, user_name="", history=None):
        return self.appointment_actions.eliminar(text, user_name=user_name)

    def _ver_citas(self, text, entities, intent, confidence, user_name="", history=None):
        result = self.appointment_actions.listar(user_name=user_name)
        result["target"] = "appointments"
        return result

    def _crear_paciente(self, text, entities, intent, confidence, user_name="", history=None):
        # Buscar datos pendientes del flujo de agendar cita en el contexto del historial
        pending_data = {}
        if history:
            for msg in reversed(history):
                ctx = msg.get("context") if isinstance(msg, dict) else None
                if ctx and ctx.get("pending", {}).get("intent") == "agendar_cita":
                    pending_data = ctx["pending"].get("entities", {}).get("_pending_patient", {})
                    if pending_data:
                        break
        if pending_data and (not entities.get("_pending_patient")):
            entities["_pending_patient"] = pending_data
        return self.patient_actions.prefill_patient(text, entities=entities, user_name=user_name)

    def _eliminar_paciente(self, text, entities, intent, confidence, user_name="", history=None):
        return self.patient_actions.eliminar(text, user_name=user_name)

    def _ver_pacientes(self, text, entities, intent, confidence, user_name="", history=None):
        result = self.patient_actions.listar(user_name=user_name)
        result["target"] = "patients"
        return result

    def _crear_medico(self, text, entities, intent, confidence, user_name="", history=None):
        return self.doctor_actions.prefill_doctor(text, user_name=user_name)

    def _eliminar_medico(self, text, entities, intent, confidence, user_name="", history=None):
        return self.doctor_actions.eliminar(text, user_name=user_name)

    def _ver_medicos(self, text, entities, intent, confidence, user_name="", history=None):
        result = self.doctor_actions.listar(user_name=user_name)
        result["target"] = "doctors"
        return result

    def _consultar_doctor(self, text, entities, intent, confidence, user_name="", history=None):
        specialty = entities.get("specialty")
        return self.doctor_actions.consultar_especialidad(specialty, user_name=user_name)

    def _predecir_riesgo(self, text, entities, intent, confidence, user_name="", history=None):
        return collect_risk_data(text, entities, user_name=user_name)

    def _confirmar_cita(self, text, entities, intent, confidence, user_name="", history=None):
        return self.appointment_actions.confirm(text, entities, user_name=user_name)

    # ─── Acciones simples (respuestas fijas) ──────────────────

    def _emergencia(self, text, entities, intent, confidence, user_name="", history=None):
        nombre = user_name or "Usuario"
        return {
            "type": "emergency",
            "message": (
                f"⚠️ ATENCIÓN {nombre}: Se ha detectado una posible emergencia.\n"
                "Derivando al área de Emergencia.\n"
                "Números de emergencia:\n"
                "  Hospital de Pichanaki: (064) 123-456\n"
                "  SAMU: 106\n"
                "  Bomberos: 116"
            ),
            "action": "emergencia",
        }

    def _informacion(self, text, entities, intent, confidence, user_name="", history=None):
        nombre = user_name or "Usuario"
        return {
            "type": "info",
            "message": (
                f"Claro {nombre}, aquí tienes la información del Hospital de Pichanaki:\n"
                "  Dirección: Av. La Salud S/N, Pichanaki, Chanchamayo, Junín\n"
                "  Horario: Lun-Vie 7:00-18:00 | Sáb 7:00-13:00\n"
                "  Emergencia: 24 horas\n"
                "  Teléfono: (064) 123-456\n"
                "  Seguros: SIS, EsSalud, Privado"
            ),
            "action": "informacion_servicios",
        }

    def _resultados(self, text, entities, intent, confidence, user_name="", history=None):
        try:
            paciente = self.patient_actions._buscar(text, user_name=user_name)
            return {
                "type": "info",
                "message": f"{paciente.first_name} {paciente.last_name}, para consultar tus resultados de laboratorio acércate al laboratorio del hospital con tu DNI y código de cita.",
                "action": "resultados_lab",
            }
        except Exception:
            return {"type": "info", "message": "Para consultar resultados, dime el nombre del paciente o su DNI. Por ejemplo: 'Maria Lopez' o 'DNI 12345678'", "action": "resultados_lab"}

    def _queja(self, text, entities, intent, confidence, user_name="", history=None):
        return {
            "type": "info",
            "message": (
                "Hemos registrado tu queja o reclamo.\n"
                "Para darle seguimiento formal, acércate a la oficina de Atención al Usuario:\n"
                "  - Presenta tu DNI\n"
                "  - Describe el incidente por escrito\n"
                "  - Recibirás un número de expediente\n\n"
                "Libro de Reclamaciones disponible en la entrada principal."
            ),
            "action": "queja_reclamo",
        }

    def _navegar(self, text, entities, intent, confidence, user_name="", history=None):
        nombre = user_name or "Usuario"
        target = detectar_navegacion(text)
        if not target:
            return {
                "type": "info",
                "message": f"{nombre}, ¿a qué sección quieres ir? Puedo llevarte a: Dashboard, Médicos, Pacientes, Citas o IA.",
                "action": "navegar",
            }
        return {
            "type": "navigation",
            "message": f"Claro {nombre}, abriendo {nombre_pagina(target)}...",
            "action": f"navigate:{target}",
            "target": target,
        }

    def _default_handler(self, text, entities, intent, confidence, user_name="", history=None):
        nombre = user_name or "Usuario"
        return {
            "type": "info",
            "message": (
                f"{nombre}, no entendí completamente tu solicitud.\n\n"
                f"Puedes pedirme cosas como:\n"
                f"  • **Agendar**, **cancelar**, **consultar** o **reprogramar** una cita\n"
                f"  • **Ver** pacientes, médicos o citas\n"
                f"  • **Crear** un paciente o médico nuevo\n"
                f"  • **Navegar** al Dashboard, Pacientes, Médicos o Citas\n\n"
                f"Intenta ser más específico."
            ),
            "action": intent,
        }

    def _ultima_intencion_util(self, history: list) -> str | None:
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("intent") in _INTENCIONES_UTIL:
                return msg["intent"]
        return None

    process_message_with_db = process_message
