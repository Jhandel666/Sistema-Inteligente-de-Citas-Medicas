from __future__ import annotations

import re
import unicodedata

from app.ml.inference.risk_service import AppointmentRiskService
from app.services.assistant.intent_detector import _ESPECIALIDADES_SINONIMOS, _NUMEROS


def _norm(t: str) -> str:
    return unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode("ascii")


_RISK_FIELDS = [
    ("patient_age", [
        "la **edad** del paciente",
        "¿cuántos años tiene el paciente?",
        "la edad en años",
    ]),
    ("gender", [
        "el **sexo** (masculino o femenino)",
        "¿el paciente es hombre o mujer?",
        "el género del paciente",
    ]),
    ("specialty", [
        "la **especialidad** médica (ej: Medicina General, Cardiología)",
        "¿qué especialidad médica?",
    ]),
    ("priority", [
        "la **prioridad** de la cita (normal, baja, media, alta, urgente)",
        "¿qué prioridad tiene la cita?",
    ]),
    ("appointment_shift", [
        "el **turno** (mañana o tarde)",
        "¿es cita de mañana o tarde?",
    ]),
    ("previous_no_show_count", [
        "el número de **faltas previas** del paciente",
        "¿cuántas citas ha perdido el paciente anteriormente?",
        "¿cuántas inasistencias ha tenido?",
    ]),
    ("distance_km", [
        "la **distancia al hospital en km**",
        "¿a cuántos km del hospital vive?",
    ]),
    ("days_until_appointment", [
        "los **días hasta la cita**",
        "¿cuántos faltan para la cita?",
    ]),
    ("waiting_minutes_estimated", [
        "los **minutos de espera estimados**",
        "¿cuánto tiempo de espera estimas en minutos?",
    ]),
]


def _extract_strong(text: str, field: str):
    t = _norm(text)
    if field == "patient_age":
        m = re.search(r"\b(\d{1,3})\s*(?:años|año|anios|anio|edad)\b", t)
        if m:
            v = int(m.group(1))
            if 0 <= v <= 120:
                return v
    elif field == "gender":
        if re.search(r"\b(masculino|varon|hombre)\b", t):
            return "masculino"
        if re.search(r"\b(femenino|mujer)\b", t):
            return "femenino"
    elif field == "specialty":
        for especialidad, keywords in _ESPECIALIDADES_SINONIMOS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(_norm(kw))}\b", t):
                    return especialidad
    elif field == "priority":
        for p in ["urgente", "alta", "media", "normal", "baja"]:
            if re.search(rf"\b{re.escape(p)}\b", t):
                return p
    elif field == "appointment_shift":
        if re.search(r"\b(mañana|manana)\b", t):
            return "manana"
        if re.search(r"\btarde\b", t):
            return "tarde"
    elif field == "previous_no_show_count":
        # BUG 4: "ninguna falta" → 0
        if re.search(r"\b(cero|ninguna?)\s+(faltas?|inasistencias?)\b", t):
            return 0
        m = re.search(r"\b(\d{1,2})\s*(?:faltas?|no.?shows?|inasistencias?|cancelaciones?)\b", t)
        if m:
            return int(m.group(1))
        m = re.search(r"(?:de\s+las?\s+)?(\d{1,2})\s*(?:citas?)\b.*?(?:inasistio|inasistió|falto|faltó|perdio|perdió)\s*(?:a\s+)?(\d{1,2})", t)
        if m:
            return int(m.group(2))
    elif field == "distance_km":
        m = re.search(r"(?:a\s+)?(\d+(?:\.\d+)?)\s*(?:km|kilometros|kilometros|kms)", t)
        if m:
            return float(m.group(1))
    elif field == "days_until_appointment":
        m = re.search(r"\b(\d{1,3})\s*(?:dias?|dias?)\b", t)
        if m:
            return int(m.group(1))
    elif field == "waiting_minutes_estimated":
        m = re.search(r"\b(\d{1,3})\s*(?:minutos?|mins?)\b", t)
        if m:
            return int(m.group(1))
    return None


def _extract_permissive(text: str, field: str):
    t = _norm(text)
    if field == "patient_age":
        nums = [int(x) for x in re.findall(r"\b(\d{1,3})\b", t) if 1 <= int(x) <= 120]
        if nums:
            return nums[0]
        for palabra, num in _NUMEROS.items():
            if re.search(rf"\b{re.escape(palabra)}\b", t) and 1 <= num <= 120:
                return num
    elif field == "gender":
        if re.search(r"\b(masculino|varon|hombre)\b", t):
            return "masculino"
        if re.search(r"\b(femenino|mujer)\b", t):
            return "femenino"
    elif field == "specialty":
        for especialidad, keywords in _ESPECIALIDADES_SINONIMOS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(_norm(kw))}\b", t):
                    return especialidad
    elif field == "priority":
        for p in ["urgente", "alta", "media", "normal", "baja"]:
            if re.search(rf"\b{re.escape(p)}\b", t):
                return p
    elif field == "appointment_shift":
        if re.search(r"\b(mañana|manana|tarde)\b", t):
            return "manana" if re.search(r"\b(mañana|manana)\b", t) else "tarde"
    elif field == "previous_no_show_count":
        nums = [int(x) for x in re.findall(r"\b(\d{1,2})\b", t) if 0 <= int(x) <= 50]
        if nums:
            return nums[0]
    elif field == "distance_km":
        m = re.search(r"(\d+(?:\.\d+)?)", t)
        if m:
            return float(m.group(1))
    elif field == "days_until_appointment":
        nums = [int(x) for x in re.findall(r"\b(\d{1,3})\b", t) if 1 <= int(x) <= 365]
        if nums:
            return nums[0]
        for palabra, num in _NUMEROS.items():
            if re.search(rf"\b{re.escape(palabra)}\b", t):
                return num
    elif field == "waiting_minutes_estimated":
        nums = [int(x) for x in re.findall(r"\b(\d{1,3})\b", t) if 1 <= int(x) <= 240]
        if nums:
            return nums[0]
    return None


def _describe_risk(risk_level: str, confidence: float) -> tuple[str, str]:
    level_map = {
        "bajo": ("BAJO", "CITA SEGURA", "es bajo. La cita es segura"),
        "medio": ("MEDIO", "CITA CON PRECAUCION", "es medio. Se recomienda confirmar la cita"),
        "alto": ("ALTO", "RIESGO ELEVADO", "es alto. Se recomienda llamar al paciente para confirmar"),
        "muy alto": ("MUY ALTO", "CITA NO SEGURA", "es muy alto. Se recomienda llamar al paciente para confirmar"),
    }
    label, icon, desc = level_map.get(risk_level, ("DESCONOCIDO", "", "no se pudo determinar"))
    c = round(confidence * 100)
    msg_text = (
        f"\n\n*Riesgo de inasistencia: {label}*\n"
        f"{icon}\n"
        f"Confianza: {c}%"
    )
    msg_voice = f"El riesgo de inasistencia {desc} con una confianza del {c} por ciento."
    return msg_text, msg_voice


def _pick_prompt(field: str, step_index: int) -> str:
    opts = dict(_RISK_FIELDS).get(field, ["ese dato"])
    return opts[step_index % len(opts)]


def collect_risk_data(text: str, entities: dict, user_name: str = "") -> dict:
    nombre = user_name or "Usuario"

    risk_data = entities.get("risk_data", {})

    current_step = 0
    for i, (field, _) in enumerate(_RISK_FIELDS):
        if risk_data.get(field) is None:
            current_step = i
            break

    for i, (field, _) in enumerate(_RISK_FIELDS):
        current = risk_data.get(field)
        if current is not None:
            continue
        val = _extract_strong(text, field)
        if val is not None:
            risk_data[field] = val
            continue
        if i == current_step:
            val = _extract_permissive(text, field)
            if val is not None:
                risk_data[field] = val

    missing = [(f, _pick_prompt(f, i)) for i, (f, _) in enumerate(_RISK_FIELDS) if risk_data.get(f) is None]

    if not missing:
        try:
            risk = AppointmentRiskService()
            result = risk.predict_risk(
                patient_age=risk_data["patient_age"],
                gender=risk_data["gender"],
                specialty=risk_data["specialty"],
                priority=risk_data["priority"],
                appointment_shift=risk_data["appointment_shift"],
                previous_no_show_count=risk_data["previous_no_show_count"],
                distance_km=risk_data["distance_km"],
                days_until_appointment=risk_data["days_until_appointment"],
                waiting_minutes_estimated=risk_data["waiting_minutes_estimated"],
            )
        except Exception:
            return {
                "type": "error",
                "action": "predecir_riesgo",
                "message": f"{nombre}, ocurrió un error al ejecutar el modelo de predicción.",
            }

        if result.get("model") == "not_loaded":
            return {
                "type": "error",
                "action": "predecir_riesgo",
                "message": f"{nombre}, el modelo de riesgo no está disponible en este momento.",
            }

        entities["risk_data"] = risk_data
        msg_text, msg_voice = _describe_risk(result["risk_level"], result["confidence"])
        return {
            "type": "success",
            "action": "predecir_riesgo",
            "message": f"{nombre}, aquí tienes el resultado:\n{msg_text}",
            "voice": f"{nombre}, {msg_voice}",
            "risk_data": risk_data,
            "risk_result": result,
            "risk_result_display": {
                "risk_level": result["risk_level"],
                "confidence": result["confidence"],
            },
        }

    next_field, next_prompt = missing[0]
    total = len(_RISK_FIELDS)
    done = total - len(missing)

    entities["risk_data"] = risk_data

    prompts = [
        f"{nombre}, necesito algunos datos. {next_prompt}",
        f"{nombre}, sigamos con la predicción. {next_prompt}",
        f"{nombre}, vamos avanzando ({done}/{total}). {next_prompt}",
        f"{nombre}, una pregunta más. {next_prompt}",
        f"{nombre}, continuemos. {next_prompt}",
        f"{nombre}, siguiente: {next_prompt}",
    ]
    msg = prompts[done % len(prompts)]

    return {
        "type": "info",
        "action": "predecir_riesgo",
        "message": msg,
    }
