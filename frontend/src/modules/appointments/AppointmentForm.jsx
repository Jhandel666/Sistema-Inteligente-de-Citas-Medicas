import { useEffect, useState } from "react";
import { getPatients } from "../patients/patientService";
import { getDoctors } from "../doctors/doctorService";
import { predictAppointmentRisk } from "./appointmentService";
import { useFormFilling } from "../../context/FormFillingContext";

function toGenderSelect(v) {
  if (!v) return "";
  const low = String(v).toLowerCase();
  if (low === "masculino" || low === "m") return "M";
  if (low === "femenino" || low === "f") return "F";
  return v;
}

const initialRiskData = {
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

const calcularEdad = (fechaNacimiento) => {
  if (!fechaNacimiento) return "";
  const hoy = new Date();
  const nacimiento = new Date(fechaNacimiento);
  let edad = hoy.getFullYear() - nacimiento.getFullYear();
  const mes = hoy.getMonth() - nacimiento.getMonth();
  if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
    edad--;
  }
  return edad;
};

const calcularDiasHastaCita = (fechaCita) => {
  if (!fechaCita) return "";
  const hoy = new Date();
  const cita = new Date(fechaCita);
  const diff = cita - hoy;
  return diff > 0 ? Math.round(diff / (1000 * 60 * 60 * 24)) : 0;
};

const pareceHoraOFecha = (valor) => {
  const texto = String(valor || "").trim().toLowerCase();
  if (!texto) return false;
  if (/^\d{1,2}:\d{2}$/.test(texto)) return true;
  if (/^\d{1,2}(\s*)(am|pm)$/.test(texto)) return true;
  if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return true;
  if (/^\d{1,2}\s+de\s+[a-záéíóúñ]+/.test(texto)) return true;
  return false;
};

const normalizarValoresCita = (values = {}) => {
  const motivo = values.reason ?? values.motivo ?? "";

  return {
    patient_id: String(values.patient_id ?? values.paciente_id ?? ""),
    doctor_id: String(values.doctor_id ?? values.medico_id ?? ""),
    scheduled_at: values.scheduled_at ?? values.programada_en ?? "",
    reason: pareceHoraOFecha(motivo) ? "" : motivo,
  };
};

function AppointmentForm({ onPredict, initialData, onCancelEdit }) {
  const { session, riskData: ctxRiskData } = useFormFilling();
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [predicting, setPredicting] = useState(false);
  const [formData, setFormData] = useState({
    patient_id: "",
    doctor_id: "",
    scheduled_at: "",
    reason: "",
  });
  const [riskData, setRiskData] = useState(initialRiskData);

  useEffect(() => {
    if (initialData) {
      setFormData({
        patient_id: String(initialData.paciente_id ?? initialData.patient_id ?? ""),
        doctor_id: String(initialData.medico_id ?? initialData.doctor_id ?? ""),
        scheduled_at: initialData.programada_en ?? initialData.scheduled_at ?? "",
        reason: initialData.motivo ?? initialData.reason ?? "",
      });
    }
  }, [initialData]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const patientsData = await getPatients();
        const doctorsData = await getDoctors();
        setPatients(patientsData);
        setDoctors(doctorsData);
      } catch {
        alert("Error al cargar pacientes y médicos");
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    if (session && session.entity === "appointment") {
      const vals = normalizarValoresCita(session.values);
      setFormData((prev) => ({ ...prev, ...vals }));
    }
  }, [session?.values]);

  useEffect(() => {
    if (ctxRiskData) {
      setRiskData((prev) => ({ ...prev, ...ctxRiskData }));
    }
  }, [ctxRiskData]);

  useEffect(() => {
    const paciente = patients.find((p) => String(p.id) === formData.patient_id);
    if (paciente) {
      setRiskData((prev) => ({
        ...prev,
        edad_paciente: calcularEdad(paciente.fecha_nacimiento ?? paciente.birth_date),
        genero: toGenderSelect(paciente.genero ?? paciente.gender ?? ""),
      }));
    }
  }, [formData.patient_id, patients]);

  useEffect(() => {
    const medico = doctors.find((d) => String(d.id) === formData.doctor_id);
    if (medico) {
      setRiskData((prev) => ({
        ...prev,
        especialidad: medico.especialidad ?? medico.specialty ?? "",
      }));
    }
  }, [formData.doctor_id, doctors]);

  useEffect(() => {
    setRiskData((prev) => ({
      ...prev,
      dias_hasta_cita: calcularDiasHastaCita(formData.scheduled_at),
    }));
  }, [formData.scheduled_at]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRiskChange = (e) => {
    setRiskData({ ...riskData, [e.target.name]: e.target.value });
  };

  const submit = async (e) => {
    e.preventDefault();

    const formPayload = {
      paciente_id: Number(formData.patient_id),
      medico_id: Number(formData.doctor_id),
      programada_en: formData.scheduled_at,
      motivo: formData.reason,
    };

    const riskPayload = {
      edad_paciente: Number(riskData.edad_paciente),
      genero: riskData.genero,
      especialidad: riskData.especialidad,
      prioridad: riskData.prioridad,
      turno_cita: riskData.turno_cita,
      conteo_inasistencias_previas: Number(riskData.conteo_inasistencias_previas),
      distancia_km: Number(riskData.distancia_km),
      dias_hasta_cita: Number(riskData.dias_hasta_cita),
      minutos_espera_estimados: Number(riskData.minutos_espera_estimados),
    };

    setPredicting(true);
    try {
      const result = await predictAppointmentRisk(riskPayload);
      onPredict({
        formData: formPayload,
        riskPayload,
        result,
        editingId: initialData?.id,
        isEditing: !!initialData,
      });
    } catch (error) {
      alert("Error al predecir riesgo: " + JSON.stringify(error.response?.data || error.message));
    } finally {
      setPredicting(false);
    }

    if (!initialData) {
      setFormData({ patient_id: "", doctor_id: "", scheduled_at: "", reason: "" });
      setRiskData(initialRiskData);
    }
  };

  const isFilling = session && session.entity === "appointment" && !session.completed;

  return (
    <form onSubmit={submit} className="space-y-3">
      {isFilling && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs px-3 py-2 rounded-lg mb-2">
          La IA está llenando el formulario paso a paso
        </div>
      )}

      <select name="patient_id" value={formData.patient_id} onChange={handleChange} className="w-full border p-3 rounded-lg" required>
        <option value="">Seleccione paciente</option>
        {patients.map((p) => (
          <option key={p.id} value={p.id}>
            {p.nombres} {p.apellidos} - DNI {p.numero_documento}
          </option>
        ))}
      </select>

      <select name="doctor_id" value={formData.doctor_id} onChange={handleChange} className="w-full border p-3 rounded-lg" required>
        <option value="">Seleccione médico</option>
        {doctors.map((d) => (
          <option key={d.id} value={d.id}>
            Dr(a). {d.nombres} {d.apellidos} - {d.especialidad}
          </option>
        ))}
      </select>

      <div>
        <label className="block mb-2 font-medium text-gray-700">Fecha y hora de la cita</label>
        <input type="datetime-local" name="scheduled_at" value={formData.scheduled_at} onChange={handleChange} min={new Date().toISOString().slice(0, 16)} className="w-full border p-3 rounded-lg" required />
      </div>

      <textarea name="reason" value={formData.reason} onChange={handleChange} className="w-full border p-3 rounded-lg" placeholder="Motivo de la cita" required />

      <div className="border-t pt-4 mt-4">
        <h3 className="font-semibold text-gray-700 mb-3">Predicción de Riesgo - Modelo de Entrenamiento IA</h3>
        <div className="grid grid-cols-3 gap-4">
          <input type="number" name="edad_paciente" value={riskData.edad_paciente} onChange={handleRiskChange} className="border p-3 rounded-lg" placeholder="Edad del paciente" min="0" max="120" required />

          <select name="genero" value={riskData.genero} onChange={handleRiskChange} className="border p-3 rounded-lg" required>
            <option value="">Sexo</option>
            <option value="M">Masculino</option>
            <option value="F">Femenino</option>
          </select>

          <input
            type="text"
            name="especialidad"
            value={riskData.especialidad}
            readOnly
            className="border p-3 rounded-lg bg-gray-100 text-gray-700"
            placeholder="Especialidad autoasignada por el médico"
            required
          />

          <select name="prioridad" value={riskData.prioridad} onChange={handleRiskChange} className="border p-3 rounded-lg" required>
            <option value="">Prioridad</option>
            <option value="baja">Baja</option>
            <option value="media">Media</option>
            <option value="alta">Alta</option>
          </select>

          <select name="turno_cita" value={riskData.turno_cita} onChange={handleRiskChange} className="border p-3 rounded-lg" required>
            <option value="">Turno</option>
            <option value="manana">Mañana</option>
            <option value="tarde">Tarde</option>
            <option value="noche">Noche</option>
          </select>

          <input type="number" name="conteo_inasistencias_previas" value={riskData.conteo_inasistencias_previas} onChange={handleRiskChange} className="border p-3 rounded-lg" placeholder="Faltas previas" min="0" required />
          <input type="number" step="0.1" name="distancia_km" value={riskData.distancia_km} onChange={handleRiskChange} className="border p-3 rounded-lg" placeholder="Distancia km" min="0" required />
          <input type="number" name="dias_hasta_cita" value={riskData.dias_hasta_cita} onChange={handleRiskChange} className="border p-3 rounded-lg" placeholder="Días hasta la cita" min="0" required />
          <input type="number" name="minutos_espera_estimados" value={riskData.minutos_espera_estimados} onChange={handleRiskChange} className="border p-3 rounded-lg" placeholder="Espera estimada (min)" min="0" required />
        </div>
      </div>

      <div className="flex gap-3">
        {onCancelEdit && (
          <button type="button" onClick={onCancelEdit} className="w-full bg-gray-400 text-white p-3 rounded-lg">
            Cancelar
          </button>
        )}
        <button className="w-full bg-green-600 text-white p-3 rounded-lg" disabled={predicting}>
          {predicting ? "Analizando riesgo..." : initialData ? "Actualizar cita" : "Crear cita"}
        </button>
      </div>
    </form>
  );
}

export default AppointmentForm;