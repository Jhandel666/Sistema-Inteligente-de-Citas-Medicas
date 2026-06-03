PARCHE 100 FUNCIONAL - BD/ORM/DOCKER/SESIONES/NOTIFICACIONES

Reemplazar respetando rutas:

1) app/models/inteligencia.py
   - Alinea ORM con el SQL real citas_medicas (5).sql.
   - Evita tablas duplicadas: registros_notificaciones y registro_modelos_ml.
   - Evita columnas inexistentes en predicciones_riesgo_citas.

2) app/repositories/inteligencia_repository.py
   - Guarda predicciones usando nombre_modelo.
   - Guarda/recupera sesiones_asistente desde BD.
   - Registra notificaciones usando registros_notificaciones.
   - Registra modelos ML usando registro_modelos_ml.

3) app/api/v1/endpoints/assistant.py
   - Recupera contexto desde sesiones_asistente antes de usar memoria RAM.
   - Sigue guardando estado del asistente en BD.

4) app/api/v1/endpoints/appointments.py
   - Al confirmar cita y generar ticket registra bitácora de notificaciones.

5) database/citas_medicas_phpmyadmin.sql
   - Copia del SQL actual correcto para Docker.
   - Agrega historial_asistencia si falta.

COMANDOS:

uvicorn app.main:app --reload --reload-dir app

Para Docker nuevo:
docker compose down -v
docker compose up --build

NOTA: docker compose down -v borra el volumen MySQL. Usarlo solo si quieres reinicializar desde cero.
