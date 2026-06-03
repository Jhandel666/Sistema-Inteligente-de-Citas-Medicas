from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


FEATURE_COLUMNS = [
    "edad_paciente",
    "genero",
    "especialidad",
    "prioridad",
    "turno_cita",
    "num_inasistencias_previas",
    "distancia_km",
    "dias_para_cita",
    "minutos_espera_estimados",
]

TARGET_COLUMN = "nivel_riesgo"

ALIASES_TO_SPANISH = {
    "patient_age": "edad_paciente",
    "gender": "genero",
    "specialty": "especialidad",
    "priority": "prioridad",
    "appointment_shift": "turno_cita",
    "previous_no_show_count": "num_inasistencias_previas",
    "distance_km": "distancia_km",
    "days_until_appointment": "dias_para_cita",
    "waiting_minutes_estimated": "minutos_espera_estimados",
}


class ServicioRiesgoCitas:
    _model_registered: bool = False

    def __init__(self) -> None:
        self.model = None
        self.encoders = None

        self.models_dir = Path(__file__).resolve().parents[1] / "models"
        self.model_path = self.models_dir / "no_show_risk_model.pkl"
        self.encoders_path = self.models_dir / "no_show_encoders.pkl"

        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists() or not self.encoders_path.exists():
            logger.warning("Modelo de riesgo no encontrado.")
            return

        with open(self.model_path, "rb") as file:
            self.model = pickle.load(file)

        with open(self.encoders_path, "rb") as file:
            self.encoders = pickle.load(file)

        logger.info("Modelo ML de riesgo cargado correctamente.")

    def predecir_riesgo(
        self,
        edad_paciente: int | None = None,
        genero: str | None = None,
        especialidad: str | None = None,
        prioridad: str | None = None,
        turno_cita: str | None = None,
        num_inasistencias_previas: int | None = None,
        distancia_km: float | None = None,
        dias_para_cita: int | None = None,
        minutos_espera_estimados: int | None = None,
        **kwargs,
    ) -> dict[str, str | float]:
        """
        Predice riesgo usando los nombres reales del sistema en español.
        También acepta alias antiguos en inglés para no romper endpoints existentes.
        """
        datos = {
            "edad_paciente": edad_paciente,
            "genero": genero,
            "especialidad": especialidad,
            "prioridad": prioridad,
            "turno_cita": turno_cita,
            "num_inasistencias_previas": num_inasistencias_previas,
            "distancia_km": distancia_km,
            "dias_para_cita": dias_para_cita,
            "minutos_espera_estimados": minutos_espera_estimados,
        }

        for alias, spanish_name in ALIASES_TO_SPANISH.items():
            if datos.get(spanish_name) is None and alias in kwargs:
                datos[spanish_name] = kwargs[alias]

        datos["edad_paciente"] = int(datos["edad_paciente"] or 0)
        datos["genero"] = str(datos["genero"] or "M")
        datos["especialidad"] = str(datos["especialidad"] or "Medicina General")
        datos["prioridad"] = str(datos["prioridad"] or "media")
        datos["turno_cita"] = str(datos["turno_cita"] or "manana")
        datos["num_inasistencias_previas"] = int(datos["num_inasistencias_previas"] or 0)
        datos["distancia_km"] = float(datos["distancia_km"] or 0.0)
        datos["dias_para_cita"] = int(datos["dias_para_cita"] or 0)
        datos["minutos_espera_estimados"] = int(datos["minutos_espera_estimados"] or 0)

        if self.model is None or self.encoders is None:
            return self._fallback_local(datos)

        x = np.array(
            [[
                datos["edad_paciente"],
                self._encode("genero", datos["genero"]),
                self._encode("especialidad", datos["especialidad"]),
                self._encode("prioridad", datos["prioridad"]),
                self._encode("turno_cita", datos["turno_cita"]),
                datos["num_inasistencias_previas"],
                datos["distancia_km"],
                datos["dias_para_cita"],
                datos["minutos_espera_estimados"],
            ]]
        )

        probabilities = self.model.predict_proba(x)[0]
        predicted_index = int(np.argmax(probabilities))
        confidence = float(np.max(probabilities))

        risk_level = self.encoders[TARGET_COLUMN].inverse_transform([predicted_index])[0]

        confianza = round(confidence, 4)
        return {
            "nivel_riesgo": risk_level,
            "confianza": confianza,
            "probabilidad_riesgo": confianza,
            "modelo": "random_forest_ml",
            # Compatibilidad con código anterior en inglés
            "risk_level": risk_level,
            "confidence": confianza,
            "model": "random_forest_ml",
        }

    def _fallback_local(self, datos: dict) -> dict[str, str | float]:
        score = 0.0
        previas = datos["num_inasistencias_previas"]
        distancia = datos["distancia_km"]
        espera = datos["minutos_espera_estimados"]
        dias = datos["dias_para_cita"]
        prioridad = str(datos["prioridad"]).lower()

        if previas >= 3:
            score += 0.35
        elif previas == 2:
            score += 0.25
        elif previas == 1:
            score += 0.12

        if distancia >= 20:
            score += 0.20
        elif distancia >= 10:
            score += 0.12
        elif distancia >= 5:
            score += 0.06

        if espera >= 60:
            score += 0.15
        elif espera >= 30:
            score += 0.08

        if dias >= 30:
            score += 0.10
        elif dias >= 15:
            score += 0.06

        if prioridad in ("baja", "normal"):
            score += 0.06
        elif prioridad in ("alta", "urgente"):
            score -= 0.05

        score = max(0.0, min(score, 0.95))

        if score >= 0.65:
            nivel = "alto"
        elif score >= 0.35:
            nivel = "medio"
        else:
            nivel = "bajo"

        confianza = round(score, 4)
        return {
            "nivel_riesgo": nivel,
            "confianza": confianza,
            "probabilidad_riesgo": confianza,
            "modelo": "fallback_local_sin_pkl",
            "risk_level": nivel,
            "confidence": confianza,
            "model": "fallback_local_sin_pkl",
        }

    def _encode(self, column: str, value: str) -> int:
        encoder = self.encoders[column]
        normalized_value = str(value).strip().lower()

        if normalized_value not in encoder.classes_:
            logger.warning("Valor no visto por el modelo: %s=%s. Se usará clase 0.", column, normalized_value)
            return 0

        return int(encoder.transform([normalized_value])[0])


# Compatibilidad con nombre anterior.
AppointmentRiskService = ServicioRiesgoCitas
ServicioRiesgoCitas.predict_risk = ServicioRiesgoCitas.predecir_riesgo
