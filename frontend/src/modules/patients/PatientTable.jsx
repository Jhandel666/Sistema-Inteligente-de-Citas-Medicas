function obtenerPaciente(paciente = {}) {
  const nombres = paciente.nombres ?? paciente.first_name ?? "";
  const apellidos = paciente.apellidos ?? paciente.last_name ?? "";
  return {
    id: paciente.id,
    nombreCompleto: `${nombres} ${apellidos}`.trim() || "—",
    numeroDocumento: paciente.numero_documento ?? paciente.document_number ?? "—",
    correo: paciente.correo ?? paciente.correo_electronico ?? paciente.email ?? "—",
    telefono: paciente.telefono ?? paciente.phone ?? "—",
  };
}

function PatientTable({ patients = [], onEdit, onDelete }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border text-sm">
        <thead>
          <tr className="bg-blue-900 text-white">
            <th className="p-3 text-left font-semibold">ID</th>
            <th className="p-3 text-left font-semibold">Paciente</th>
            <th className="p-3 text-left font-semibold">DNI</th>
            <th className="p-3 text-left font-semibold">Correo</th>
            <th className="p-3 text-left font-semibold">Teléfono</th>
            <th className="p-3 text-left font-semibold">Acciones</th>
          </tr>
        </thead>

        <tbody>
          {patients.map((patient, i) => {
            const p = obtenerPaciente(patient);
            return (
              <tr key={p.id} className={`border-b transition hover:bg-blue-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                <td className="p-3 text-gray-500">{p.id}</td>
                <td className="p-3 font-medium">{p.nombreCompleto}</td>
                <td className="p-3">{p.numeroDocumento}</td>
                <td className="p-3">{p.correo}</td>
                <td className="p-3">{p.telefono}</td>
                <td className="p-3 whitespace-nowrap">
                  <button onClick={() => onEdit(patient)} className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1.5 rounded text-xs font-medium transition mr-1">
                    Editar
                  </button>
                  <button onClick={() => onDelete(p.id)} className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded text-xs font-medium transition">
                    Eliminar
                  </button>
                </td>
              </tr>
            );
          })}

          {patients.length === 0 && (
            <tr>
              <td colSpan="6" className="p-6 text-center text-gray-400 bg-white">
                No hay pacientes registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default PatientTable;
