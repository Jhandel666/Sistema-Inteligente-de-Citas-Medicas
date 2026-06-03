from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


class MedicalIntentService:
    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None
        self.label_encoder = None
        self.max_length = 25

        self.models_dir = Path(__file__).resolve().parents[1] / "models"
        self.model_path = self.models_dir / "intent_lstm_model.keras"
        self.tokenizer_path = self.models_dir / "tokenizer.pkl"
        self.label_encoder_path = self.models_dir / "label_encoder.pkl"
        self.config_path = self.models_dir / "intent_lstm_config.json"

        self._load_deep_learning_model()

    def _load_deep_learning_model(self) -> None:
        try:
            if (
                self.model_path.exists()
                and self.tokenizer_path.exists()
                and self.label_encoder_path.exists()
            ):
                from tensorflow.keras.models import load_model

                self.model = load_model(self.model_path)

                if self.config_path.exists():
                    try:
                        config = json.loads(self.config_path.read_text(encoding="utf-8"))
                        self.max_length = int(config.get("max_length", self.max_length))
                    except Exception:
                        pass

                with open(self.tokenizer_path, "rb") as file:
                    self.tokenizer = pickle.load(file)

                with open(self.label_encoder_path, "rb") as file:
                    self.label_encoder = pickle.load(file)

                logger.info("Modelo LSTM cargado correctamente.")
            else:
                logger.warning("Modelo LSTM no encontrado. Usando reglas básicas.")
        except Exception as error:
            logger.error("No se pudo cargar el modelo LSTM: %s", error)
            self.model = None
            self.tokenizer = None
            self.label_encoder = None

    def predict_intent(self, text: str) -> dict[str, str | float]:
        clean_text = text.lower().strip()

        if self.model and self.tokenizer and self.label_encoder:
            return self._predict_with_lstm(clean_text)

        return self._predict_with_rules(clean_text)

    def _predict_with_lstm(self, text: str) -> dict[str, str | float]:
        from tensorflow.keras.preprocessing.sequence import pad_sequences

        sequence = self.tokenizer.texts_to_sequences([text])

        padded = pad_sequences(
            sequence,
            maxlen=self.max_length,
            padding="post",
            truncating="post",
        )

        prediction = self.model.predict(padded, verbose=0)[0]

        predicted_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))

        intent = self.label_encoder.inverse_transform([predicted_index])[0]

        return {
            "intent": intent,
            "confidence": round(confidence, 4),
            "model": "lstm_deep_learning",
        }

    def _predict_with_rules(self, text: str) -> dict[str, str | float]:
        if any(word in text for word in ["reservar", "agendar", "sacar", "separar", "consulta", "crear cita", "cita médica", "cita medica"]):
            return {
                "intent": "agendar_cita",
                "confidence": 0.75,
                "model": "rules_fallback",
            }

        if any(word in text for word in ["cancelar", "anular", "eliminar"]):
            return {
                "intent": "cancelar_cita",
                "confidence": 0.82,
                "model": "rules_fallback",
            }

        if any(word in text for word in ["confirmar", "ticket", "estado", "consultar"]):
            return {
                "intent": "consultar_cita",
                "confidence": 0.78,
                "model": "rules_fallback",
            }

        if any(word in text for word in ["reprogramar", "cambiar", "mover", "fecha"]):
            return {
                "intent": "reprogramar_cita",
                "confidence": 0.77,
                "model": "rules_fallback",
            }

        return {
            "intent": "desconocido",
            "confidence": 0.50,
            "model": "rules_fallback",
        }