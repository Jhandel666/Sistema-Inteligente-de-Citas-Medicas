import { useEffect, useState } from "react";
import { useFormFilling } from "../../context/FormFillingContext";

const EMPTY_DOCTOR = {
  nombres: "",
  apellidos: "",
  especialidad: "",
  correo: "",
};

function normalizarMedico(datos = {}) {
  return {
    nombres: datos.nombres ?? datos.first_name ?? "",
    apellidos: datos.apellidos ?? datos.last_name ?? "",
    especialidad: datos.especialidad ?? datos.specialty ?? "",
    correo: datos.correo ?? datos.correo_electronico ?? datos.email ?? "",
  };
}

function DoctorForm({ selectedDoctor, onSave, onCancel }) {
  const { session } = useFormFilling();
  const [formData, setFormData] = useState(EMPTY_DOCTOR);

  useEffect(() => {
    if (selectedDoctor) setFormData(normalizarMedico(selectedDoctor));
    else setFormData(EMPTY_DOCTOR);
  }, [selectedDoctor]);

  useEffect(() => {
    if (session && (session.entity === "doctor" || session.entity === "medico" || session.entity === "médico")) {
      setFormData((prev) => ({ ...prev, ...normalizarMedico(session.values) }));
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
      especialidad: formData.especialidad.trim(),
      correo: formData.correo.trim(),
    });
  };

  const isFilling = session && (session.entity === "doctor" || session.entity === "medico" || session.entity === "médico") && !session.completed;

  return (
    <form onSubmit={submit} className="space-y-3">
      {isFilling && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs px-3 py-2 rounded-lg mb-2">
          La IA está llenando el formulario paso a paso
        </div>
      )}
      <input id="medico-nombres" name="nombres" value={formData.nombres} onChange={handleChange} autoComplete="given-name" className="w-full border p-3 rounded-lg" placeholder="Nombres del médico" required />
      <input id="medico-apellidos" name="apellidos" value={formData.apellidos} onChange={handleChange} autoComplete="family-name" className="w-full border p-3 rounded-lg" placeholder="Apellidos del médico" required />
      <input id="medico-especialidad" name="especialidad" value={formData.especialidad} onChange={handleChange} autoComplete="organization-title" className="w-full border p-3 rounded-lg" placeholder="Especialidad" required />
      <input id="medico-correo" type="email" name="correo" value={formData.correo} onChange={handleChange} autoComplete="email" className="w-full border p-3 rounded-lg" placeholder="Correo del médico" required />
      <div className="flex gap-3">
        <button className="bg-blue-700 text-white px-5 py-3 rounded-lg">
          {selectedDoctor ? "Actualizar médico" : "Guardar médico"}
        </button>
        {selectedDoctor && (
          <button type="button" onClick={onCancel} className="bg-gray-500 text-white px-5 py-3 rounded-lg">
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}

export default DoctorForm;
