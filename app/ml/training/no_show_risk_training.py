from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "citas_medicas_pichanaki_junin_5000.csv"
)

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
MODEL_PATH = MODEL_DIR / "no_show_risk_model.pkl"
ENCODERS_PATH = MODEL_DIR / "no_show_encoders.pkl"
METADATA_PATH = MODEL_DIR / "no_show_model_metadata.json"
REPORT_PATH = Path(__file__).resolve().parent / "training_report.md"

# El sistema trabaja en español. Estas son las columnas reales del CSV.
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

CATEGORICAL_COLUMNS = [
    "genero",
    "especialidad",
    "prioridad",
    "turno_cita",
]

NUMERIC_COLUMNS = [
    "edad_paciente",
    "num_inasistencias_previas",
    "distancia_km",
    "dias_para_cita",
    "minutos_espera_estimados",
]


# Alias para aceptar datos antiguos o datos del frontend en inglés sin romper compatibilidad.
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
    "risk_level": "nivel_riesgo",
}


def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra alias conocidos y garantiza columnas españolas."""
    df = df.rename(columns={k: v for k, v in ALIASES_TO_SPANISH.items() if k in df.columns})
    return df


def train_no_show_model() -> None:
    df = pd.read_csv(DATASET_PATH)
    df = normalizar_dataframe(df)

    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise ValueError(
            "Faltan columnas requeridas: "
            + ", ".join(missing_columns)
            + f"\nColumnas encontradas: {list(df.columns)}"
        )

    df = df[required_columns].dropna().copy()

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna().copy()

    encoders: dict[str, LabelEncoder] = {}

    for column in CATEGORICAL_COLUMNS:
        encoder = LabelEncoder()
        df[column] = encoder.fit_transform(df[column].astype(str).str.strip().str.lower())
        encoders[column] = encoder

    target_encoder = LabelEncoder()
    df[TARGET_COLUMN] = target_encoder.fit_transform(df[TARGET_COLUMN].astype(str).str.strip().str.lower())
    encoders[TARGET_COLUMN] = target_encoder

    x = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_split=5,
        random_state=42,
        class_weight="balanced",
    )

    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    report = classification_report(y_test, predictions, target_names=target_encoder.classes_)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    with open(MODEL_PATH, "wb") as file:
        pickle.dump(model, file)

    with open(ENCODERS_PATH, "wb") as file:
        pickle.dump(encoders, file)

    metadata = {
        "tipo_proyecto": "ML",
        "algoritmo": "RandomForestClassifier",
        "librerias": ["numpy", "pandas", "scikit-learn"],
        "dataset": str(DATASET_PATH.name),
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "numeric_columns": NUMERIC_COLUMNS,
        "accuracy": round(float(accuracy), 4),
        "mse": round(float(mse), 4),
        "clases": list(target_encoder.classes_),
        "observacion": "Modelo entrenado con columnas en español, sin IA externa ni APIs de terceros.",
    }

    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    REPORT_PATH.write_text(
        "# Reporte de entrenamiento ML - Riesgo de inasistencia\n\n"
        f"- Tipo de proyecto: Machine Learning tabular\n"
        f"- Dataset: `{DATASET_PATH.name}`\n"
        f"- Algoritmo: `RandomForestClassifier`\n"
        f"- Librerías evidenciadas: `numpy`, `pandas`, `scikit-learn`\n"
        f"- Variable objetivo: `{TARGET_COLUMN}`\n"
        f"- Variables predictoras: `{', '.join(FEATURE_COLUMNS)}`\n"
        f"- Accuracy: `{accuracy:.4f}`\n"
        f"- MSE: `{mse:.4f}`\n\n"
        "## Classification report\n\n"
        "```text\n"
        f"{report}\n"
        "```\n\n"
        "Nota: Es un proyecto ML, no DL; por eso no requiere gráfico de red neuronal.\n",
        encoding="utf-8",
    )

    print("Accuracy:", round(float(accuracy), 4))
    print("MSE:", round(float(mse), 4))
    print(report)
    print("Modelo de riesgo guardado correctamente.")
    print(MODEL_PATH)


if __name__ == "__main__":
    train_no_show_model()
