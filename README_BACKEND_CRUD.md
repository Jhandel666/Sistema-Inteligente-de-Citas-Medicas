# Backend completo CRUD - Hospital de Pichanaki

## Ejecutar backend

Desde la raiz del proyecto:

```powershell
.venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000/docs
```

## Endpoints principales

### Pacientes
- GET `/api/v1/patients/`
- POST `/api/v1/patients/`
- GET `/api/v1/patients/{patient_id}`
- PUT `/api/v1/patients/{patient_id}`
- DELETE `/api/v1/patients/{patient_id}`

### Medicos
- GET `/api/v1/doctors/`
- POST `/api/v1/doctors/`
- GET `/api/v1/doctors/{doctor_id}`
- PUT `/api/v1/doctors/{doctor_id}`
- DELETE `/api/v1/doctors/{doctor_id}`

### Citas y tickets
- GET `/api/v1/appointments/`
- POST `/api/v1/appointments/`
- GET `/api/v1/appointments/{appointment_id}`
- PUT `/api/v1/appointments/{appointment_id}`
- DELETE `/api/v1/appointments/{appointment_id}`
- POST `/api/v1/appointments/{appointment_id}/confirm`
- POST `/api/v1/appointments/{appointment_id}/cancel`
- GET `/api/v1/appointments/tickets/`
- GET `/api/v1/appointments/tickets/{ticket_id}`
- GET `/api/v1/appointments/tickets/code/{code}`

### IA / Voz
- POST `/api/v1/appointments/voice/intent`

## Nota
Este backend esta ajustado para MySQL local por XAMPP usando `.env`.
