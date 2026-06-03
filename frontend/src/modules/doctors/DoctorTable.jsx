function obtenerMedico(medico = {}) {
  const nombres = medico.nombres ?? medico.first_name ?? "";
  const apellidos = medico.apellidos ?? medico.last_name ?? "";
  return {
    id: medico.id,
    nombreCompleto: `${nombres} ${apellidos}`.trim() || "—",
    especialidad: medico.especialidad ?? medico.specialty ?? "—",
    correo: medico.correo ?? medico.correo_electronico ?? medico.email ?? "—",
  };
}

function DoctorTable({ doctors = [], onEdit, onDelete }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border text-sm">
        <thead>
          <tr className="bg-blue-900 text-white">
            <th className="p-3 text-left font-semibold">ID</th>
            <th className="p-3 text-left font-semibold">Médico</th>
            <th className="p-3 text-left font-semibold">Especialidad</th>
            <th className="p-3 text-left font-semibold">Correo</th>
            <th className="p-3 text-left font-semibold">Acciones</th>
          </tr>
        </thead>

        <tbody>
          {doctors.map((doctor, i) => {
            const d = obtenerMedico(doctor);
            return (
              <tr key={d.id} className={`border-b transition hover:bg-blue-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                <td className="p-3 text-gray-500">{d.id}</td>
                <td className="p-3 font-medium">{d.nombreCompleto}</td>
                <td className="p-3">{d.especialidad}</td>
                <td className="p-3">{d.correo}</td>
                <td className="p-3 whitespace-nowrap">
                  {onEdit && (
                    <button type="button" onClick={() => onEdit(doctor)} className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1.5 rounded text-xs font-medium transition mr-1">
                      Editar
                    </button>
                  )}
                  {onDelete && (
                    <button type="button" onClick={() => onDelete(d.id)} className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded text-xs font-medium transition">
                      Eliminar
                    </button>
                  )}
                  {!onEdit && !onDelete && <span className="text-gray-400 text-xs italic">Solo lectura</span>}
                </td>
              </tr>
            );
          })}

          {doctors.length === 0 && (
            <tr>
              <td colSpan="5" className="p-6 text-center text-gray-400 bg-white">
                No hay médicos registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default DoctorTable;
