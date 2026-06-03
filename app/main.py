from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 - registra modelos SQLAlchemy antes de create_all
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.base import Base
from app.db.session import engine

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    description=(
        "Sistema Inteligente para la Gestion de Citas Medicas - Hospital de Pichanaki. "
        "Autor: Jhandel Jesus Chavez Miranda."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://sistema-inteligente-de-citas-medica.vercel.app",
        "https://sistema-inteligente-de-citas-medicas.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Iniciando %s", settings.app_name)
    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos inicializada correctamente")


app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "message": "Sistema Inteligente de Citas Medicas operativo - Hospital de Pichanaki"
    }
