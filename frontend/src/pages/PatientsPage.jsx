import { useEffect, useState } from "react";
import PageCard from "../components/ui/PageCard";
import PatientForm from "../modules/patients/PatientForm";
import PatientTable from "../modules/patients/PatientTable";
import {
  createPatient,
  deletePatient,
  getPatients,
  updatePatient,
} from "../modules/patients/patientService";
import {
  exportPatientsCsv,
  exportPatientsPdf,
} from "../modules/reports/patientReportService";

function PatientsPage() {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);

  const loadPatients = async () => {
    try {
      const data = await getPatients();
      setPatients(data);
    } catch (error) {
      alert("Error al listar pacientes");
    }
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleSave = async (formData) => {
    try {
      if (selectedPatient) {
        await updatePatient(selectedPatient.id, formData);
        alert("Paciente actualizado correctamente");
      } else {
        await createPatient(formData);
        alert("Paciente registrado correctamente");
      }

      setSelectedPatient(null);
      loadPatients();
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
    const confirmDelete = confirm("¿Seguro que deseas eliminar este paciente?");
    if (!confirmDelete) return;

    try {
      await deletePatient(id);
      alert("Paciente eliminado correctamente");
      loadPatients();
    } catch (error) {
      alert(
        JSON.stringify(
          error.response?.data || "No se pudo eliminar el paciente",
          null,
          2
        )
      );
    }
  };

  return (
    <div>
      <PageCard title={selectedPatient ? "Editar Paciente" : "Registrar Paciente"}>
        <PatientForm
          selectedPatient={selectedPatient}
          onSave={handleSave}
          onCancel={() => setSelectedPatient(null)}
        />
      </PageCard>

      <PageCard title="Listado de Pacientes" fullWidth>
        <div className="flex gap-3 mb-4">
          <button
            type="button"
            onClick={() => exportPatientsPdf(patients)}
            className="bg-purple-700 text-white px-4 py-2 rounded"
          >
            Exportar PDF
          </button>

          <button
            type="button"
            onClick={() => exportPatientsCsv(patients)}
            className="bg-green-700 text-white px-4 py-2 rounded"
          >
            Exportar CSV
          </button>
        </div>

        <PatientTable
          patients={patients}
          onEdit={setSelectedPatient}
          onDelete={handleDelete}
        />
      </PageCard>
    </div>
  );
}

export default PatientsPage;