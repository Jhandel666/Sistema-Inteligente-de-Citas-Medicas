from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.schemas.appointment import CitaCrear
from app.schemas.doctor import MedicoCrear
from app.schemas.patient import PacienteCrear


_FIELD_META: dict[str, dict[str, Any]] = {
    "nombres": {"label": "Nombres", "type": "text", "placeholder": "Ej: Juan Carlos"},
    "apellidos": {"label": "Apellidos", "type": "text", "placeholder": "Ej: Pérez García"},
    "numero_documento": {"label": "DNI", "type": "text", "placeholder": "12345678"},
    "correo": {"label": "Correo electrónico", "type": "email", "placeholder": "correo@ejemplo.com"},
    "telefono": {"label": "Teléfono", "type": "tel", "placeholder": "999888777"},
    "fecha_nacimiento": {"label": "Fecha de nacimiento", "type": "date", "placeholder": ""},
    "genero": {"label": "Sexo", "type": "select", "options": [
        {"value": "masculino", "label": "Masculino"},
        {"value": "femenino", "label": "Femenino"},
    ], "placeholder": "Seleccione sexo"},
    "especialidad": {"label": "Especialidad", "type": "text", "placeholder": "Ej: Cardiología"},
    "paciente_id": {"label": "Paciente", "type": "select", "placeholder": "Seleccione paciente"},
    "medico_id": {"label": "Médico", "type": "select", "placeholder": "Seleccione médico"},
    "programada_en": {"label": "Fecha y hora de la cita", "type": "datetime-local", "placeholder": ""},
    "motivo": {"label": "Motivo de la cita", "type": "textarea", "placeholder": "Ej: Control de rutina"},

    # Compatibilidad temporal con nombres anteriores del frontend.
    "first_name": {"label": "Nombres", "type": "text", "placeholder": "Ej: Juan Carlos"},
    "last_name": {"label": "Apellidos", "type": "text", "placeholder": "Ej: Pérez García"},
    "document_number": {"label": "DNI", "type": "text", "placeholder": "12345678"},
    "email": {"label": "Correo electrónico", "type": "email", "placeholder": "correo@ejemplo.com"},
    "phone": {"label": "Teléfono", "type": "tel", "placeholder": "999888777"},
    "birth_date": {"label": "Fecha de nacimiento", "type": "date", "placeholder": ""},
    "gender": {"label": "Sexo", "type": "select", "options": [
        {"value": "masculino", "label": "Masculino"},
        {"value": "femenino", "label": "Femenino"},
    ], "placeholder": "Seleccione sexo"},
    "specialty": {"label": "Especialidad", "type": "text", "placeholder": "Ej: Cardiología"},
    "patient_id": {"label": "Paciente", "type": "select", "placeholder": "Seleccione paciente"},
    "doctor_id": {"label": "Médico", "type": "select", "placeholder": "Seleccione médico"},
    "scheduled_at": {"label": "Fecha y hora de la cita", "type": "datetime-local", "placeholder": ""},
    "reason": {"label": "Motivo de la cita", "type": "textarea", "placeholder": "Ej: Control de rutina"},
}


_SCHEMAS: dict[str, type] = {
    "paciente": PacienteCrear,
    "medico": MedicoCrear,
    "médico": MedicoCrear,
    "cita": CitaCrear,

    # Compatibilidad temporal con nombres anteriores del frontend.
    "patient": PacienteCrear,
    "doctor": MedicoCrear,
    "appointment": CitaCrear,
}


def _field_meta(name: str) -> dict[str, Any]:
    return dict(_FIELD_META.get(name, {"label": name.replace("_", " ").title(), "type": "text", "placeholder": ""}))


def get_form_schema(entity: str, db: Session | None = None) -> dict[str, Any]:
    schema_cls = _SCHEMAS.get(entity)
    if not schema_cls:
        raise ValueError(f"Entidad desconocida: {entity}")

    json_schema = schema_cls.model_json_schema()
    properties = json_schema.get("properties", {})
    required = set(json_schema.get("required", []))

    fields: list[dict[str, Any]] = []
    for name, prop in properties.items():
        meta = _field_meta(name)
        field: dict[str, Any] = {
            "name": name,
            "label": meta["label"],
            "type": meta["type"],
            "required": name in required,
            "placeholder": meta["placeholder"],
        }
        if "minLength" in prop:
            field["min_length"] = prop["minLength"]
        if "maxLength" in prop:
            field["max_length"] = prop["maxLength"]
        if "format" in prop and prop["format"] == "date":
            field["type"] = "date"

        if name in ("paciente_id", "patient_id", "medico_id", "doctor_id"):
            field["type"] = "select"
            if db is not None:
                field["options"] = _load_related_options(name, db)

        if "options" in meta:
            field["options"] = meta["options"]

        fields.append(field)

    return {"entity": entity, "fields": fields}


def _load_related_options(field_name: str, db: Session) -> list[dict[str, Any]]:
    if field_name in ("paciente_id", "patient_id"):
        from app.models.patient import Paciente
        rows = db.query(Paciente).order_by(Paciente.apellidos).all()
        return [
            {"value": p.id, "label": f"{p.nombres} {p.apellidos} - DNI {p.numero_documento}"}
            for p in rows
        ]

    if field_name in ("medico_id", "doctor_id"):
        from app.models.doctor import Medico
        rows = db.query(Medico).order_by(Medico.apellidos).all()
        return [
            {"value": d.id, "label": f"Dr(a). {d.nombres} {d.apellidos} - {d.especialidad}"}
            for d in rows
        ]

    return []
