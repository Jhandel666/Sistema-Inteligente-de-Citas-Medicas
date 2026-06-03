from fastapi import APIRouter

from app.api.v1.endpoints import appointments, assistant, auth, doctors, health, patients


api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(
    appointments.router,
    prefix="/appointments",
    tags=["appointments"],
)
api_router.include_router(
    assistant.router,
    prefix="/assistant",
    tags=["assistant"],
)
