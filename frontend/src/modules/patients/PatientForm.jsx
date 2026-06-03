import { useEffect, useState } from "react";
import { useFormFilling } from "../../context/FormFillingContext";

const EMPTY_PATIENT = {
  nombres: "",
  apellidos: "",
  numero_documento: "",
  correo: "",
  telefono: "",
  fecha_nacimiento: "",
  genero: "",
};

function normalizarPaciente(datos = {}) {
  return {
    nombres: datos.nombres ?? datos.first_name ?? "",
    apellidos: datos.apellidos ?? datos.last_name ?? "",
    numero_documento: datos.numero_documento ?? datos.document_number ?? "",
    correo: datos.correo ?? datos.correo_electronico ?? datos.email ?? "",
    telefono: datos.telefono ?? datos.phone ?? "",
    fecha_nacimiento: datos.fecha_nacimiento ?? datos.birth_date ?? "",
    genero: datos.genero ?? datos.gender ?? "",
  };
}

function normalizarValoresSesion(values = {}) {
  return normalizarPaciente(values);
}

function PatientForm({ selectedPatient, onSave, onCancel }) {
  const { session } = useFormFilling();
  const [formData, setFormData] = useState(EMPTY_PATIENT);

  useEffect(() => {
    if (selectedPatient) {
      setFormData(normalizarPaciente(selectedPatient));
    } else {
      setFormData(EMPTY_PATIENT);
    }
  }, [selectedPatient]);

  useEffect(() => {
    if (session && (session.entity === "patient" || session.entity === "paciente")) {
      setFormData((prev) => ({ ...prev, ...normalizarValoresSesion(session.values) }));
    }
  }, [session?.values, session?.entity]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const submit = (e) => {
    e.preventDefault();
    onSave({
      nombres: formData.nombres.trim(),
      apellidos: formData.apellidos.trim(),
      numero_documento: formData.numero_documento.trim(),
      correo: formData.correo.trim(),
      telefono: formData.telefono.trim(),
      fecha_nacimiento: formData.fecha_nacimiento,
      genero: formData.genero || null,
    });
  };

  const isFilling = session && (session.entity === "patient" || session.entity === "paciente") && !session.completed;

  return (
    <form onSubmit={submit} className="space-y-3">
      {isFilling && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs px-3 py-2 rounded-lg mb-2">
          La IA está llenando el formulario paso a paso
        </div>
      )}

      <input id="paciente-nombres" name="nombres" value={formData.nombres} onChange={handleChange} autoComplete="given-name" className="w-full border p-3 rounded-lg" placeholder="Nombres" required />
      <input id="paciente-apellidos" name="apellidos" value={formData.apellidos} onChange={handleChange} autoComplete="family-name" className="w-full border p-3 rounded-lg" placeholder="Apellidos" required />
      <input id="paciente-documento" name="numero_documento" value={formData.numero_documento} onChange={handleChange} autoComplete="off" className="w-full border p-3 rounded-lg" placeholder="DNI" required />
      <input id="paciente-correo" type="email" name="correo" value={formData.correo} onChange={handleChange} autoComplete="email" className="w-full border p-3 rounded-lg" placeholder="Correo" required />
      <input id="paciente-telefono" name="telefono" value={formData.telefono} onChange={handleChange} autoComplete="tel" pattern="9[0-9]{8}" title="Debe tener 9 dígitos y empezar con 9" className="w-full border p-3 rounded-lg" placeholder="Teléfono" required />

      <div>
        <label htmlFor="paciente-fecha-nacimiento" className="block mb-2 font-medium text-gray-700">
          Fecha de nacimiento
        </label>
        <input id="paciente-fecha-nacimiento" type="date" name="fecha_nacimiento" value={formData.fecha_nacimiento} onChange={handleChange} autoComplete="bday" className="w-full border p-3 rounded-lg" required />
      </div>

      <select id="paciente-genero" name="genero" value={formData.genero || ""} onChange={handleChange} autoComplete="sex" className="w-full border p-3 rounded-lg">
        <option value="">Sexo / género</option>
        <option value="M">Masculino</option>
        <option value="F">Femenino</option>
      </select>

      <div className="flex gap-3">
        <button className="bg-green-600 text-white px-5 py-3 rounded-lg">
          {selectedPatient ? "Actualizar paciente" : "Guardar paciente"}
        </button>
        {selectedPatient && (
          <button type="button" onClick={onCancel} className="bg-gray-500 text-white px-5 py-3 rounded-lg">
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}

export default PatientForm;
