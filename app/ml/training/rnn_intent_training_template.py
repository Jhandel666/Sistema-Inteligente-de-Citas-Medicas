from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense, Embedding, Bidirectional, Dropout
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

BASE_DIR = Path(__file__).resolve().parent
DATASET_CSV_PATH = Path(__file__).resolve().parents[1] / "datasets" / "citas_medicas_pichanaki_junin_5000.csv"
INTENT_JSON_PATH = BASE_DIR / "intent_dataset.json"
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
MODEL_PATH = MODEL_DIR / "intent_lstm_model.keras"
TOKENIZER_PATH = MODEL_DIR / "tokenizer.pkl"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"
CONFIG_PATH = MODEL_DIR / "intent_lstm_config.json"

MAX_WORDS = 5000
MAX_LENGTH = 25
EPOCHS = 20
BATCH_SIZE = 32


def _load_from_csv() -> tuple[list[str], list[str]]:
    if not DATASET_CSV_PATH.exists():
        return [], []
    df = pd.read_csv(DATASET_CSV_PATH)
    if "intent" not in df.columns:
        return [], []
    text_col = "text" if "text" in df.columns else "voice_text"
    if text_col not in df.columns:
        return [], []
    df = df[[text_col, "intent"]].dropna()
    return df[text_col].astype(str).tolist(), df["intent"].astype(str).tolist()


def _load_from_json() -> tuple[list[str], list[str]]:
    if not INTENT_JSON_PATH.exists():
        return [], []
    raw = json.loads(INTENT_JSON_PATH.read_text(encoding="utf-8"))
    texts: list[str] = []
    labels: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            text = item.get("text") or item.get("phrase") or item.get("utterance")
            intent = item.get("intent") or item.get("label")
            if text and intent:
                texts.append(str(text))
                labels.append(str(intent))
    elif isinstance(raw, dict):
        for intent, phrases in raw.items():
            if isinstance(phrases, list):
                for phrase in phrases:
                    texts.append(str(phrase))
                    labels.append(str(intent))
    return texts, labels


def load_dataset() -> tuple[list[str], list[str]]:
    csv_texts, csv_labels = _load_from_csv()
    json_texts, json_labels = _load_from_json()
    texts = csv_texts + json_texts
    labels = csv_labels + json_labels
    if not texts:
        raise FileNotFoundError("No hay datos de entrenamiento para intención LSTM.")
    return texts, labels


def build_lstm_model(vocab_size: int, max_length: int, num_classes: int) -> Sequential:
    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=128, input_length=max_length),
        Bidirectional(LSTM(128, return_sequences=False)),
        Dropout(0.35),
        Dense(64, activation="relu"),
        Dropout(0.25),
        Dense(num_classes, activation="softmax"),
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train_model() -> None:
    print("Cargando dataset de intenciones...")
    texts, labels = load_dataset()
    print(f"Total ejemplos: {len(texts)}")

    tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    x = pad_sequences(sequences, maxlen=MAX_LENGTH, padding="post", truncating="post")

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)
    num_classes = len(label_encoder.classes_)
    vocab_size = min(MAX_WORDS, len(tokenizer.word_index) + 1)

    print(f"Vocabulario: {vocab_size}")
    print(f"Clases: {num_classes} -> {list(label_encoder.classes_)}")

    stratify = y if min(pd.Series(y).value_counts()) >= 2 else None
    x_train, x_val, y_train, y_val = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=stratify
    )

    model = build_lstm_model(vocab_size, MAX_LENGTH, num_classes)
    model.summary()

    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True)],
        verbose=1,
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)
    with open(TOKENIZER_PATH, "wb") as file:
        pickle.dump(tokenizer, file)
    with open(LABEL_ENCODER_PATH, "wb") as file:
        pickle.dump(label_encoder, file)
    CONFIG_PATH.write_text(json.dumps({"max_length": MAX_LENGTH}, indent=2), encoding="utf-8")

    print("Entrenamiento LSTM finalizado.")
    print(f"Modelo: {MODEL_PATH}")
    print(f"Tokenizer: {TOKENIZER_PATH}")
    print(f"LabelEncoder: {LABEL_ENCODER_PATH}")


if __name__ == "__main__":
    train_model()
