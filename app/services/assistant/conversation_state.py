from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy
from typing import Any


@dataclass
class ConversationState:
    intent: str | None = None
    entity: str | None = None
    step: str | None = None
    values: dict[str, Any] = field(default_factory=dict)
    draft_appointment: dict[str, Any] | None = None
    risk_data: dict[str, Any] | None = None
    risk_result: dict[str, Any] | None = None
    waiting_decision: bool = False
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def touch(self) -> None:
        self.updated_at = datetime.utcnow().isoformat()

    def clear(self) -> None:
        self.intent = None
        self.entity = None
        self.step = None
        self.values.clear()
        self.draft_appointment = None
        self.risk_data = None
        self.risk_result = None
        self.waiting_decision = False
        self.touch()

    def as_pending_context(self) -> dict[str, Any]:
        entities = deepcopy(self.values)

        if self.draft_appointment:
            entities["_draft_appointment"] = deepcopy(self.draft_appointment)
        if self.risk_data:
            entities["risk_data"] = deepcopy(self.risk_data)
        if self.risk_result:
            entities["risk_result"] = deepcopy(self.risk_result)
        if self.step:
            entities["_step"] = self.step

        return {
            "pending": {
                "intent": self.intent,
                "entity": self.entity,
                "entities": entities,
                "updated_at": self.updated_at,
            }
        }


class ConversationStateStore:
    """Estado conversacional simple en memoria.

    Devuelve objetos ConversationState porque app/api/v1/endpoints/assistant.py
    usa atributos como stored_state.intent. Las funciones de abajo devuelven
    diccionarios porque assistant_service.py trabaja con context["pending"].
    """

    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}

    def get(self, user_key: str = "default") -> ConversationState:
        if user_key not in self._states:
            self._states[user_key] = ConversationState()
        return self._states[user_key]

    def reset(self, user_key: str = "default") -> ConversationState:
        self._states[user_key] = ConversationState()
        return self._states[user_key]

    def update(self, user_key: str = "default", **kwargs: Any) -> ConversationState:
        state = self.get(user_key)

        if kwargs.get("intent") is not None:
            state.intent = kwargs["intent"]
        if kwargs.get("entity") is not None:
            state.entity = kwargs["entity"]
        if kwargs.get("step") is not None:
            state.step = kwargs["step"]

        values = kwargs.get("values") or kwargs.get("entities")
        if isinstance(values, dict):
            state.values.update(deepcopy(values))

        if kwargs.get("draft_appointment") is not None:
            state.draft_appointment = deepcopy(kwargs["draft_appointment"])
        if kwargs.get("risk_data") is not None:
            state.risk_data = deepcopy(kwargs["risk_data"])
        if kwargs.get("risk_result") is not None:
            state.risk_result = deepcopy(kwargs["risk_result"])
        if kwargs.get("waiting_decision") is not None:
            state.waiting_decision = bool(kwargs["waiting_decision"])

        state.touch()
        return state


conversation_state_store = ConversationStateStore()


PERSISTENT_ENTITY_KEYS = {
    "_pending_patient",
    "_patient_step",
    "_pending_doctor",
    "_doctor_step",
    "_pending_risk",
    "_draft_appointment",
    "_original_text",
    "_decision_text",
    "risk_data",
    "risk_result",
    "patient_id",
    "doctor_id",
    "date",
    "time",
    "reason",
    "specialty",
    "patient_name",
    "doctor_name",
}


def get_pending(context: dict | None = None) -> dict[str, Any]:
    if not context:
        return {}

    pending = context.get("pending") or {}
    return pending if isinstance(pending, dict) else {}


def get_entities(pending: dict | None = None) -> dict[str, Any]:
    if not pending:
        return {}

    entities = pending.get("entities") or {}
    return deepcopy(entities) if isinstance(entities, dict) else {}


def merge_persistent_entities(current: dict | None, stored: dict | None) -> dict[str, Any]:
    merged = dict(current or {})
    stored = stored or {}

    for key, value in stored.items():
        if key in PERSISTENT_ENTITY_KEYS and key not in merged:
            merged[key] = deepcopy(value)

    return merged


def _clean(text: str | None) -> str:
    return (text or "").lower().strip()


def should_reset(text: str) -> bool:
    clean = _clean(text)
    return any(
        x in clean
        for x in [
            "reiniciar flujo",
            "cancelar flujo",
            "empezar de nuevo",
            "salir del flujo",
            "borrar contexto",
        ]
    )


def wants_continue(text: str) -> bool:
    clean = _clean(text)
    return any(x in clean for x in ["continuar", "sigamos", "retomar", "seguir", "continua", "continúa"])


def is_decision_for_draft(text: str, pending: dict | None = None) -> bool:
    clean = _clean(text)
    entities = get_entities(pending)

    return bool(entities.get("_draft_appointment")) and any(
        x in clean
        for x in [
            "crear cita",
            "guardar cita",
            "confirmar cita",
            "generar ticket",
            "emitir ticket",
            "ticket",
            "llamar paciente",
            "llamar",
            "cancelar",
            "no crear",
            "anular",
            "descartar",
        ]
    )


def build_pending_context(intent: str | None, entities: dict | None, text: str | None = "") -> dict[str, Any]:
    return {
        "pending": {
            "intent": intent,
            "entities": deepcopy(entities or {}),
            "text": text or "",
            "updated_at": datetime.utcnow().isoformat(),
        }
    }


def clear_context() -> dict[str, Any]:
    return {"pending": {}}
