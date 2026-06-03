import { useState, useEffect } from "react";
import { predictAppointmentRisk } from "./appointmentService";
import { useFormFilling } from "../../context/FormFillingContext";

const initialFormData = {
  edad_paciente: "",
  genero: "",
  especialidad: "",
  prioridad: "",
  turno_cita: "",
  conteo_inasistencias_previas: "",
  distancia_km: "",
  dias_hasta_cita: "",
  minutos_espera_estimados: "",
};

function normalizarRiesgo(data = {}) {
  return {
    edad_paciente: data.edad_paciente ?? data.patient_age ?? "",
    genero: data.genero ?? data.gender ?? "",
    especialidad: data.especialidad ?? data.specialty ?? "",
    prioridad: data.prioridad ?? data.priority ?? "",
    turno_cita: data.turno_cita ?? data.appointment_shift ?? "",
    conteo_inasistencias_previas: data.conteo_inasistencias_previas ?? data.previous_no_show_count ?? "",
    distancia_km: data.distancia_km ?? data.distance_km ?? "",
    dias_hasta_cita: data.dias_hasta_cita ?? data.days_until_appointment ?? "",
    minutos_espera_estimados: data.minutos_espera_estimados ?? data.waiting_minutes_estimated ?? "",
  };
}

function toRiskPayload(data, ids) {
  const payload = {
    edad_paciente: Number(data.edad_paciente),
    genero: data.genero,
    especialidad: data.especialidad,
    prioridad: data.prioridad,
    turno_cita: data.turno_cita,
    conteo_inasistencias_previas: Number(data.conteo_inasistencias_previas),
    distancia_km: Number(data.distancia_km),
    dias_hasta_cita: Number(data.dias_hasta_cita),
    minutos_espera_estimados: Number(data.minutos_espera_estimados),
  };
  if (ids?.cita_id) payload.cita_id = ids.cita_id;
  if (ids?.paciente_id) payload.paciente_id = ids.paciente_id;
  if (ids?.medico_id) payload.medico_id = ids.medico_id;
  return payload;
}

function hasAllRiskFields(data) {
  return Object.values(data).every((value) => value !== "" && value !== null && value !== undefined);
}

function obtenerResultado(resultado = {}) {
  return {
    nivel_riesgo: resultado.nivel_riesgo ?? resultado.risk_level ?? "medio",
    confianza: Number(resultado.confianza ?? resultado.confidence ?? 0),
    modelo: resultado.modelo ?? resultado.model ?? "modelo_no_disponible",
  };
}

function AppointmentRiskForm({ appointmentIds }) {
  const { riskData } = useFormFilling();
  const [formData, setFormData] = useState(initialFormData);
  const [result, setResult] = useState(null);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    if (!riskData) return;
    setFormData((prev) => ({
      ...prev,
      ...Object.fromEntries(
        Object.entries(normalizarRiesgo(riskData)).map(([k, v]) => [
          k,
          v === null || v === undefined ? "" : String(v),
        ]),
      ),
    }));
  }, [riskData]);

  useEffect(() => {
    if (!riskData) return;
    const merged = {
      ...formData,
      ...Object.fromEntries(
        Object.entries(normalizarRiesgo(riskData)).map(([k, v]) => [
          k,
          v === null || v === undefined ? "" : String(v),
        ]),
      ),
    };
    if (!hasAllRiskFields(merged)) return;

    setPredicting(true);
    predictAppointmentRisk(toRiskPayload(merged, appointmentIds))
      .then(setResult)
      .catch(() => {})
      .finally(() => setPredicting(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [riskData]);

  const handleChange = (e) => {
    setResult(null);
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const predict = async (e) => {
    e.preventDefault();

    if (!hasAllRiskFields(formData)) {
      alert("Completa todos los campos de predicción antes de calcular el riesgo.");
      return;
    }

    setPredicting(true);
    try {
      const response = await predictAppointmentRisk(toRiskPayload(formData, appointmentIds));
      setResult(response);
    } catch (error) {
      alert(JSON.stringify(error.response?.data || "Error al predecir riesgo", null, 2));
    } finally {
      setPredicting(false);
    }
  };

  const riskConfig = {
    bajo: { bg: "bg-green-100 text-green-800 border-green-300", icon: "✅", label: "ASISTIRÁ", desc: "El paciente SÍ asistirá a la cita." },
    medio: { bg: "bg-yellow-100 text-yellow-800 border-yellow-300", icon: "⚠️", label: "NO SEGURO", desc: "¿Desea llamar al paciente para confirmar?" },
    alto: { bg: "bg-red-100 text-red-800 border-red-300", icon: "❌", label: "NO ASISTIRÁ", desc: "El paciente NO asistirá a la cita." },
  };

  const resultado = result ? obtenerResultado(result) : null;
  const cfg = resultado ? riskConfig[resultado.nivel_riesgo] || riskConfig.medio : null;
  const confianzaPorcentaje = resultado ? (resultado.confianza <= 1 ? resultado.confianza * 100 : resultado.confianza) : 0;

  return (
    <div className="space-y-5">
      <form onSubmit={predict} className="grid grid-cols-3 gap-4">
        <input type="number" name="edad_paciente" value={formData.edad_paciente} onChange={handleChange} className="border p-3 rounded-lg" placeholder="Edad del paciente" min="0" max="120" required />

        <select name="genero" value={formData.genero} onChange={handleChange} className="border p-3 rounded-lg" required>
          <option value="">Sexo</option>
          <option value="M">Masculino</option>
          <option value="F">Femenino</option>
        </select>

        <input
          type="text"
          name="especialidad"
          value={formData.especialidad}
          readOnly
          className="border p-3 rounded-lg bg-gray-100 text-gray-700"
          placeholder="Especialidad autoasignada por el médico"
          required
        />

        <select name="prioridad" value={formData.prioridad} onChange={handleChange} className="border p-3 rounded-lg" required>
          <option value="">Prioridad</option>
          <option value="baja">Baja</option>
          <option value="media">Media</option>
          <option value="alta">Alta</option>
        </select>

        <select name="turno_cita" value={formData.turno_cita} onChange={handleChange} className="border p-3 rounded-lg" required>
          <option value="">Turno</option>
          <option value="manana">Mañana</option>
          <option value="tarde">Tarde</option>
        </select>

        <input type="number" name="conteo_inasistencias_previas" value={formData.conteo_inasistencias_previas} onChange={handleChange} className="border p-3 rounded-lg" placeholder="Faltas previas" min="0" required />
        <input type="number" step="0.1" name="distancia_km" value={formData.distancia_km} onChange={handleChange} className="border p-3 rounded-lg" placeholder="Distancia km" min="0" required />
        <input type="number" name="dias_hasta_cita" value={formData.dias_hasta_cita} onChange={handleChange} className="border p-3 rounded-lg" placeholder="Días hasta la cita" min="0" required />
        <input type="number" name="minutos_espera_estimados" value={formData.minutos_espera_estimados} onChange={handleChange} className="border p-3 rounded-lg" placeholder="Espera estimada" min="0" required />

        <button className="col-span-3 bg-blue-700 text-white p-3 rounded-lg" disabled={predicting}>
          {predicting ? "Prediciendo..." : "Predecir riesgo con IA"}
        </button>
      </form>

      {cfg && resultado && (
        <div className={`border p-5 rounded-xl ${cfg.bg}`}>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">{cfg.icon}</span>
            <div>
              <h3 className="text-xl font-bold">{cfg.label}</h3>
              <p className="text-sm opacity-80">{cfg.desc}</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div><strong>Riesgo:</strong> {resultado.nivel_riesgo}</div>
            <div><strong>Confianza:</strong> {confianzaPorcentaje.toFixed(1)}%</div>
            <div><strong>Modelo:</strong> {resultado.modelo}</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AppointmentRiskForm;