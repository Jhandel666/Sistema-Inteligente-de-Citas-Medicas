from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelVisualizationService:
    def __init__(self) -> None:
        self.models_dir = Path(__file__).resolve().parents[1] / "models"
        self.model_path = self.models_dir / "intent_lstm_model.keras"
        self.tokenizer_path = self.models_dir / "tokenizer.pkl"
        self.label_encoder_path = self.models_dir / "label_encoder.pkl"
        self.config_path = self.models_dir / "intent_lstm_config.json"

        self._layers_blueprint = [
            {
                "name": "Embedding",
                "type": "embedding",
                "units": "vocab_size x 128",
                "activation": None,
                "params": "5000 × 128 = 640,000",
                "description": "Convierte cada token en un vector denso de 128 dimensiones",
                "input_shape": "(25,)",
                "output_shape": "(25, 128)",
                "neurons": 128,
            },
            {
                "name": "Bidirectional LSTM",
                "type": "lstm",
                "units": "128 × 2 = 256",
                "activation": "tanh (default)",
                "params": "4 × (128 × 128 + 128 × 128 + 128) × 2 = 263,168",
                "description": "Captura dependencias secuenciales en ambas direcciones",
                "input_shape": "(25, 128)",
                "output_shape": "(256,)",
                "neurons": 256,
            },
            {
                "name": "Dropout",
                "type": "dropout",
                "units": "256",
                "activation": None,
                "params": "0 (no entrenables)",
                "rate": 0.35,
                "description": "Apaga aleatoriamente el 35% de las neuronas para evitar sobreajuste",
                "input_shape": "(256,)",
                "output_shape": "(256,)",
                "neurons": 256,
            },
            {
                "name": "Dense (ReLU)",
                "type": "dense",
                "units": 64,
                "activation": "relu",
                "params": "256 × 64 + 64 = 16,448",
                "description": "Capa fully-connected con activación ReLU para aprender representaciones de alto nivel",
                "input_shape": "(256,)",
                "output_shape": "(64,)",
                "neurons": 64,
            },
            {
                "name": "Dropout",
                "type": "dropout",
                "units": 64,
                "activation": None,
                "params": "0 (no entrenables)",
                "rate": 0.25,
                "description": "Apaga aleatoriamente el 25% de las neuronas",
                "input_shape": "(64,)",
                "output_shape": "(64,)",
                "neurons": 64,
            },
            {
                "name": "Dense (Softmax)",
                "type": "output",
                "units": "num_clases (7-9)",
                "activation": "softmax",
                "params": "64 × num_clases + num_clases",
                "description": "Capa de salida que produce una distribución de probabilidad sobre las intenciones",
                "input_shape": "(64,)",
                "output_shape": "(num_clases,)",
                "neurons": "num_clases",
            },
        ]

        self._pesos_reales = None
        self._modelo_cargado = False
        self._num_clases = 7
        self._clases = []

        self._cargar_modelo()

    def _cargar_modelo(self) -> None:
        if not self.model_path.exists():
            logger.warning("Modelo LSTM no encontrado. Usando blueprint de arquitectura.")
            return

        try:
            from tensorflow.keras.models import load_model

            model = load_model(self.model_path)
            self._modelo_cargado = True
            self._extraer_pesos(model)

            if self.label_encoder_path.exists():
                with open(self.label_encoder_path, "rb") as f:
                    le = pickle.load(f)
                self._clases = list(le.classes_)
                self._num_clases = len(self._clases)

            logger.info("Modelo LSTM cargado para visualización.")

            import gc
            del model
            gc.collect()
        except Exception as e:
            logger.error("Error cargando modelo LSTM: %s", e)

    def _extraer_pesos(self, model) -> None:
        self._pesos_reales = []
        for i, layer in enumerate(model.layers):
            pesos_capa = layer.get_weights()
            if not pesos_capa:
                continue
            entry = {"layer_index": i, "layer_name": layer.name, "weights": [], "biases": []}
            for j, w in enumerate(pesos_capa):
                arr = np.array(w)
                if len(arr.shape) == 1:
                    entry["biases"].append({
                        "shape": list(arr.shape),
                        "size": arr.shape[0],
                        "sample_values": [round(float(v), 6) for v in arr[:5].tolist()],
                        "mean": round(float(arr.mean()), 6),
                        "std": round(float(arr.std()), 6),
                        "min": round(float(arr.min()), 6),
                        "max": round(float(arr.max()), 6),
                    })
                else:
                    entry["weights"].append({
                        "shape": list(arr.shape),
                        "size": arr.shape[0] * arr.shape[1],
                        "sample_values": [[round(float(v), 6) for v in row[:3]] for row in arr[:3].tolist()],
                        "mean": round(float(arr.mean()), 6),
                        "std": round(float(arr.std()), 6),
                        "min": round(float(arr.min()), 6),
                        "max": round(float(arr.max()), 6),
                    })
            self._pesos_reales.append(entry)

    def obtener_arquitectura(self) -> dict:
        layers = []
        for i, layer in enumerate(self._layers_blueprint):
            entry = dict(layer)
            entry["index"] = i
            if entry.get("units") == "num_clases (7-9)":
                entry["units"] = self._num_clases
                entry["neurons"] = self._num_clases
                entry["params"] = f"64 × {self._num_clases} + {self._num_clases} = {64 * self._num_clases + self._num_clases:,}"
            elif isinstance(entry.get("units"), int) and entry.get("params", "").startswith("256 × 64"):
                entry["params"] = f"256 × 64 + 64 = 16,448"
            layers.append(entry)

        return {
            "modelo": "LSTM Bidirectional para Clasificación de Intenciones",
            "framework": "TensorFlow / Keras",
            "modelo_cargado": self._modelo_cargado,
            "total_params_estimados": "919,616+",
            "optimizador": "Adam",
            "loss": "sparse_categorical_crossentropy",
            "metricas": ["accuracy"],
            "num_clases": self._num_clases,
            "clases": self._clases,
            "layers": layers,
        }

    def obtener_pesos(self) -> dict:
        if not self._pesos_reales:
            return {
                "modelo_cargado": False,
                "mensaje": "El modelo LSTM no está entrenado. Entrena el modelo ejecutando el script de entrenamiento para ver pesos y sesgos reales.",
                "pesos_por_capa": [],
            }

        total_weights = 0
        total_biases = 0
        for capa in self._pesos_reales:
            for w in capa["weights"]:
                total_weights += w["size"]
            for b in capa["biases"]:
                total_biases += b["size"]

        return {
            "modelo_cargado": True,
            "total_parametros_entrenables": total_weights + total_biases,
            "resumen": {
                "total_pesos": total_weights,
                "total_sesgos": total_biases,
            },
            "pesos_por_capa": self._pesos_reales,
        }
