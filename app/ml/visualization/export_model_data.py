from __future__ import annotations

import json
from pathlib import Path

from app.ml.visualization.model_viz_service import ModelVisualizationService


def export_to_frontend() -> None:
    frontend_path = (
        Path(__file__).resolve().parents[3]
        / "frontend"
        / "src"
        / "modules"
        / "ai"
        / "model_data.json"
    )

    service = ModelVisualizationService()
    data = {
        "arquitectura": service.obtener_arquitectura(),
        "pesos": service.obtener_pesos(),
    }

    frontend_path.parent.mkdir(parents=True, exist_ok=True)
    frontend_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ Datos del modelo exportados a: {frontend_path}")
    print(f"   Arquitectura: {data['arquitectura']['modelo_cargado']}")
    if data["pesos"]["modelo_cargado"]:
        print(f"   Pesos: {data['pesos']['total_parametros_entrenables']:,} parámetros")
    else:
        print(f"   Pesos: {data['pesos']['diagnostico']}")


if __name__ == "__main__":
    export_to_frontend()
