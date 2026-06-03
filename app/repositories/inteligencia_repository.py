from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.orm import Session

from app.models.inteligencia import (
    HistorialAsistencia,
    ModeloIA,
    NotificacionCorreo,
    PrediccionRiesgoCita,
    SesionAsistente,
)


class RepositorioInteligencia:
    def __init__(self, db: Session) -> None:
        self.db = db

    def guardar_prediccion_riesgo(
        self,
        *,
        entrada: dict[str, Any],
        salida: dict[str, Any],
        cita_id: int | None = None,
        paciente_id: int | None = None,
        medico_id: int | None = None,
    ) -> PrediccionRiesgoCita:
        """Guarda la predicción usando exactamente las columnas de la BD real."""
        prediccion = PrediccionRiesgoCita(
            cita_id=cita_id,
            paciente_id=paciente_id,
            medico_id=medico_id,
            edad_paciente=int(entrada["edad_paciente"]),
            genero=str(entrada["genero"]),
            especialidad=str(entrada["especialidad"]),
            prioridad=str(entrada["prioridad"]),
            turno_cita=str(entrada["turno_cita"]),
            conteo_inasistencias_previas=int(entrada["conteo_inasistencias_previas"]),
            distancia_km=float(entrada["distancia_km"]),
            dias_hasta_cita=int(entrada["dias_hasta_cita"]),
            minutos_espera_estimados=int(entrada["minutos_espera_estimados"]),
            nivel_riesgo=str(salida.get("nivel_riesgo") or salida.get("risk_level") or "desconocido"),
            probabilidad_riesgo=float(
                salida.get("probabilidad_riesgo")
                if salida.get("probabilidad_riesgo") is not None
                else salida.get("confidence") or salida.get("confianza") or 0
            ),
            confianza=float(salida.get("confianza") or salida.get("confidence") or 0),
            nombre_modelo=str(salida.get("modelo") or salida.get("model") or "desconocido"),
        )
        self.db.add(prediccion)
        self.db.commit()
        self.db.refresh(prediccion)
        return prediccion

    def existe_prediccion_para_cita(self, cita_id: int) -> bool:
        sentencia = select(PrediccionRiesgoCita.id).where(PrediccionRiesgoCita.cita_id == cita_id).limit(1)
        return self.db.scalar(sentencia) is not None


    def obtener_ultima_prediccion_para_cita(self, cita_id: int) -> PrediccionRiesgoCita | None:
        sentencia = (
            select(PrediccionRiesgoCita)
            .where(PrediccionRiesgoCita.cita_id == cita_id)
            .order_by(PrediccionRiesgoCita.id.desc())
            .limit(1)
        )
        return self.db.scalar(sentencia)

    def eliminar_prediccion_por_cita_id(self, cita_id: int) -> None:
        sentencia = sa_delete(PrediccionRiesgoCita).where(PrediccionRiesgoCita.cita_id == cita_id)
        self.db.execute(sentencia)
        self.db.commit()

    def eliminar_notificaciones_por_cita_id(self, cita_id: int) -> None:
        sentencia = sa_delete(NotificacionCorreo).where(NotificacionCorreo.cita_id == cita_id)
        self.db.execute(sentencia)
        self.db.commit()

    def eliminar_notificaciones_por_ticket_id(self, ticket_id: int) -> None:
        sentencia = sa_delete(NotificacionCorreo).where(NotificacionCorreo.ticket_id == ticket_id)
        self.db.execute(sentencia)
        self.db.commit()

    def obtener_sesion_asistente_activa(self, clave_sesion: str) -> SesionAsistente | None:
        return self.db.scalar(
            select(SesionAsistente)
            .where(SesionAsistente.clave_sesion == clave_sesion)
            .where(SesionAsistente.esta_activa.is_(True))
            .limit(1)
        )

    def guardar_sesion_asistente(
        self,
        *,
        clave_sesion: str,
        estado_json: dict[str, Any],
        usuario_id: int | None = None,
        intencion_actual: str | None = None,
        entidad_actual: str | None = None,
        paso_actual: str | None = None,
        activa: bool = True,
    ) -> SesionAsistente:
        sesion = self.db.scalar(select(SesionAsistente).where(SesionAsistente.clave_sesion == clave_sesion))
        if sesion is None:
            sesion = SesionAsistente(clave_sesion=clave_sesion, estado_json=estado_json)
        sesion.usuario_id = usuario_id
        sesion.intencion_actual = intencion_actual
        sesion.entidad_actual = entidad_actual
        sesion.paso = paso_actual
        sesion.estado_json = estado_json or {}
        sesion.esta_activa = bool(activa)
        self.db.add(sesion)
        self.db.commit()
        self.db.refresh(sesion)
        return sesion

    def registrar_notificacion(
        self,
        *,
        destinatario: str,
        tipo_destinatario: str | None,
        asunto: str | None,
        estado_envio: str,
        cita_id: int | None = None,
        ticket_id: int | None = None,
        mensaje_error: str | None = None,
        fecha_envio: datetime | None = None,
    ) -> NotificacionCorreo:
        item = NotificacionCorreo(
            cita_id=cita_id,
            ticket_id=ticket_id,
            correo_destinatario=destinatario,
            tipo_destinatario=tipo_destinatario or "desconocido",
            asunto=asunto or "Notificación del sistema",
            estado=estado_envio,
            mensaje_error=mensaje_error,
            enviado_en=fecha_envio,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def registrar_asistencia(self, *, paciente_id: int, cita_id: int, asistio: bool) -> HistorialAsistencia:
        item = HistorialAsistencia(paciente_id=paciente_id, cita_id=cita_id, asistio=asistio)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def registrar_modelo_ia(
        self,
        *,
        nombre_modelo: str,
        tipo_modelo: str,
        ruta_modelo: str,
        ruta_dataset: str | None = None,
        caracteristicas_json: dict[str, Any] | None = None,
        metricas_json: dict[str, Any] | None = None,
        activo: bool = True,
    ) -> ModeloIA:
        modelo = ModeloIA(
            nombre_modelo=nombre_modelo,
            tipo_modelo=tipo_modelo,
            ruta_modelo=ruta_modelo,
            ruta_dataset=ruta_dataset,
            caracteristicas_json=caracteristicas_json or {},
            metricas_json=metricas_json,
            esta_activo=bool(activo),
            entrenado_en=datetime.now(UTC),
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return modelo
