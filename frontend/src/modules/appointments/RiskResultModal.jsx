const riskConfig = {
  bajo: { bg: "bg-green-100 text-green-800 border-green-300", icon: "✅", label: "ASISTIRÁ", desc: "El paciente SÍ asistirá a la cita." },
  medio: { bg: "bg-yellow-100 text-yellow-800 border-yellow-300", icon: "⚠️", label: "NO SEGURO", desc: "¿Desea llamar al paciente para confirmar?" },
  alto: { bg: "bg-red-100 text-red-800 border-red-300", icon: "❌", label: "NO ASISTIRÁ", desc: "El paciente NO asistirá a la cita." },
};

function RiskResultModal({ result, onCrear, onConfirmarTicket, onPendiente, onDescartar, editMode }) {
  const nivel = result?.nivel_riesgo || result?.risk_level || "medio";
  const confianzaRaw = result?.confianza ?? result?.confidence ?? 0;
  const confianza = confianzaRaw <= 1 ? confianzaRaw * 100 : confianzaRaw;
  const cfg = riskConfig[nivel] || riskConfig.medio;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-6 space-y-5">
        <div className={`border p-5 rounded-xl ${cfg.bg}`}>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">{cfg.icon}</span>
            <div>
              <h3 className="text-xl font-bold">{cfg.label}</h3>
              <p className="text-sm opacity-80">{cfg.desc}</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div><strong>Riesgo:</strong> {nivel}</div>
            <div><strong>Confianza:</strong> {confianza.toFixed(1)}%</div>
            <div><strong>Modelo:</strong> {result?.modelo || result?.model || "desconocido"}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button onClick={onCrear} className={`text-white p-3 rounded-lg font-semibold ${editMode ? "bg-blue-600 hover:bg-blue-700" : "bg-green-600 hover:bg-green-700"}`}>
            {editMode ? "Guardar cambios" : "Crear cita"}
          </button>
          {!editMode && (
            <button onClick={onConfirmarTicket} className="bg-blue-700 text-white p-3 rounded-lg font-semibold hover:bg-blue-800">
              + Ticket
            </button>
          )}
          {!editMode && (
            <button onClick={onPendiente} className="bg-yellow-500 text-white p-3 rounded-lg font-semibold hover:bg-yellow-600">
              Pendiente
            </button>
          )}
          <button onClick={onDescartar} className="bg-gray-300 text-gray-700 p-3 rounded-lg font-semibold hover:bg-gray-400">
            Descartar
          </button>
        </div>
      </div>
    </div>
  );
}

export default RiskResultModal;