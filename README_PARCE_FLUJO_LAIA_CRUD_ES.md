# Parche flujo LaIA según CRUD/API/BD en español

Este parche respeta los schemas y endpoints actuales del proyecto:

- PacienteCrear: nombres, apellidos, numero_documento, correo, telefono, fecha_nacimiento, genero
- MedicoCrear: nombres, apellidos, especialidad, correo
- CitaCrear: paciente_id, medico_id, programada_en, motivo
- SolicitudRiesgoCita: edad_paciente, genero, especialidad, prioridad, turno_cita, conteo_inasistencias_previas, distancia_km, dias_hasta_cita, minutos_espera_estimados

Corrige:
1. Prefill de paciente en español.
2. Prefill de médico en español, incluyendo correo cuando exista.
3. Borrador de cita en español.
4. Creación de cita desde LaIA usando CitaCrear con campos correctos.
5. Persistencia de predicción realizada por LaIA antes de confirmar/generar ticket.
6. Correos hablados y género escuchado por voz.
7. Fallback local de riesgo si aún no existen los .pkl, para no bloquear el flujo en desarrollo.

Después de reemplazar:
    uvicorn app.main:app --reload --reload-dir app

Pruebas sugeridas:
1. Crear paciente desde LaIA.
2. Crear médico desde LaIA.
3. Agendar cita para paciente existente.
4. Predicción: responder distancia, espera, inasistencias y prioridad.
5. Decir "confirmar cita" y verificar que cree cita + ticket.
