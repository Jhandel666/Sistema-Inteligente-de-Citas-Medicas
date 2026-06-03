function formatearFecha(valor) {
  if (!valor) return "—";
  try {
    return new Date(valor).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return String(valor);
  }
}

function obtenerEstado(estado) {
  const limpio = String(estado || "").toLowerCase();
  const mapa = {
    pending: "pendiente",
    confirmed: "confirmada",
    cancelled: "cancelada",
    pendiente: "pendiente",
    confirmada: "confirmada",
    cancelada: "cancelada",
  };
  return mapa[limpio] || limpio || "—";
}

function obtenerCita(item = {}) {
  const pacienteObj = item.paciente || item.patient;
  const medicoObj = item.medico || item.doctor;
  const pacienteNombre = pacienteObj ? `${pacienteObj.nombres ?? pacienteObj.first_name ?? ""} ${pacienteObj.apellidos ?? pacienteObj.last_name ?? ""}`.trim() : "";
  const medicoNombre = medicoObj ? `${medicoObj.nombres ?? medicoObj.first_name ?? ""} ${medicoObj.apellidos ?? medicoObj.last_name ?? ""}`.trim() : "";

  return {
    id: item.id,
    paciente: pacienteNombre || item.nombre_paciente || item.patient_name || `Paciente #${item.paciente_id ?? item.patient_id ?? "—"}`,
    medico: medicoNombre || item.nombre_medico || item.doctor_name || `Médico #${item.medico_id ?? item.doctor_id ?? "—"}`,
    fecha: item.programada_en ?? item.scheduled_at ?? item.fecha_hora_cita ?? "",
    estado: obtenerEstado(item.estado ?? item.status),
    motivo: item.motivo ?? item.reason ?? "—",
  };
}

function AppointmentTable({ appointments = [], onDelete, onConfirm, onEdit, onAttendance }) {
  const statusColors = {
    pendiente: "bg-yellow-100 text-yellow-800",
    confirmada: "bg-green-100 text-green-800",
    cancelada: "bg-red-100 text-red-800",
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border text-sm">
        <thead>
          <tr className="bg-blue-900 text-white">
            <th className="p-3 text-left font-semibold">ID</th>
            <th className="p-3 text-left font-semibold">Paciente</th>
            <th className="p-3 text-left font-semibold">Médico</th>
            <th className="p-3 text-left font-semibold">Fecha</th>
            <th className="p-3 text-left font-semibold">Estado</th>
            <th className="p-3 text-left font-semibold">Motivo</th>
            <th className="p-3 text-left font-semibold">Acciones</th>
          </tr>
        </thead>

        <tbody>
          {appointments.map((item, i) => {
            const cita = obtenerCita(item);
            return (
              <tr key={cita.id} className={`border-b transition hover:bg-blue-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                <td className="p-3 text-gray-500">{cita.id}</td>
                <td className="p-3 font-medium">{cita.paciente}</td>
                <td className="p-3">{cita.medico}</td>
                <td className="p-3">{formatearFecha(cita.fecha)}</td>
                <td className="p-3">
                  <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusColors[cita.estado] || "bg-gray-100 text-gray-700"}`}>
                    {cita.estado}
                  </span>
                </td>
                <td className="p-3 max-w-xs truncate">{cita.motivo}</td>
                <td className="p-3 whitespace-nowrap">
                  {onAttendance && cita.estado === "confirmada" && (
                    <>
                      <button onClick={() => onAttendance(cita.id, true)} className="bg-teal-600 hover:bg-teal-700 text-white px-3 py-1.5 rounded text-xs font-medium transition mr-1">Asistió</button>
                      <button onClick={() => onAttendance(cita.id, false)} className="bg-orange-600 hover:bg-orange-700 text-white px-3 py-1.5 rounded text-xs font-medium transition mr-1">No asistió</button>
                    </>
                  )}
                  <button onClick={() => onConfirm(cita.id)} className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded text-xs font-medium transition mr-1">Confirmar</button>
                  <button onClick={() => onEdit(cita.id)} className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-xs font-medium transition mr-1">Editar</button>
                  <button onClick={() => onDelete(cita.id)} className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded text-xs font-medium transition">Eliminar</button>
                </td>
              </tr>
            );
          })}

          {appointments.length === 0 && (
            <tr>
              <td colSpan="7" className="p-6 text-center text-gray-400 bg-white">No hay citas registradas</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default AppointmentTable;
