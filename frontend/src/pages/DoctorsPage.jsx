import { useEffect, useState } from "react";

import PageCard from "../components/ui/PageCard";
import DoctorForm from "../modules/doctors/DoctorForm";
import DoctorTable from "../modules/doctors/DoctorTable";

import {
  createDoctor,
  deleteDoctor,
  getDoctors,
  updateDoctor,
} from "../modules/doctors/doctorService";

import {
  exportDoctorsCsv,
  exportDoctorsPdf,
} from "../modules/reports/doctorReportService";

function DoctorsPage() {
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState(null);

  const loadDoctors = async () => {
    try {
      const data = await getDoctors();
      setDoctors(data);
    } catch {
      alert("Error al listar médicos");
    }
  };

  useEffect(() => {
    loadDoctors();
  }, []);

  const handleSave = async (formData) => {
    try {
      if (selectedDoctor) {
        await updateDoctor(selectedDoctor.id, formData);
        alert("Médico actualizado correctamente");
      } else {
        await createDoctor(formData);
        alert("Médico registrado correctamente");
      }

      setSelectedDoctor(null);
      await loadDoctors();
    } catch (error) {
      alert(
        JSON.stringify(
          error.response?.data || "Error desconocido",
          null,
          2
        )
      );
    }
  };

  const handleDelete = async (id) => {
    const confirmDelete = confirm("¿Seguro que deseas eliminar este médico?");
    if (!confirmDelete) return;

    try {
      await deleteDoctor(id);
      alert("Médico eliminado correctamente");
      await loadDoctors();
    } catch (error) {
      alert(
        JSON.stringify(
          error.response?.data || "No se pudo eliminar el médico",
          null,
          2
        )
      );
    }
  };

  return (
    <div>
      <PageCard title={selectedDoctor ? "Editar Médico" : "Registrar Médico"}>
        <DoctorForm
          selectedDoctor={selectedDoctor}
          onSave={handleSave}
          onCancel={() => setSelectedDoctor(null)}
        />
      </PageCard>

      <PageCard title="Listado de Médicos" fullWidth>
        <div className="flex gap-3 mb-4">
          <button
            type="button"
            onClick={() => exportDoctorsPdf(doctors)}
            className="bg-purple-700 text-white px-4 py-2 rounded"
          >
            Exportar PDF
          </button>

          <button
            type="button"
            onClick={() => exportDoctorsCsv(doctors)}
            className="bg-green-700 text-white px-4 py-2 rounded"
          >
            Exportar CSV
          </button>
        </div>

        <DoctorTable
          doctors={doctors}
          onEdit={setSelectedDoctor}
          onDelete={handleDelete}
        />
      </PageCard>
    </div>
  );
}

export default DoctorsPage;