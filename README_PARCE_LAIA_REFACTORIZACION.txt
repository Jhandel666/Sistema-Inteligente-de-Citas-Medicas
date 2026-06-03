PARCHE REFACTORIZACIÓN LAIA - FASE 1

Rutas incluidas:

frontend/src/components/chat/LaIA.jsx
frontend/src/components/chat/utils/normalizers.js
frontend/src/components/chat/utils/correctionEngine.js
frontend/src/components/chat/services/laiaApi.js
frontend/src/components/chat/hooks/useLaIAVoice.js
frontend/src/components/chat/hooks/useLaIAFlow.js

Qué hace:
1. Separa normalizadores de voz/texto.
2. Separa motor de corrección.
3. Separa llamadas API de LaIA.
4. Mantiene el flujo actual del proyecto.
5. No cambia rutas del backend.
6. Mantiene compatibilidad con campos en español e inglés.

Después de copiar:
cd frontend
npm run dev

Prueba:
- crear paciente
- corregir correo
- corregir nombre
- corregir DNI
- crear médico
