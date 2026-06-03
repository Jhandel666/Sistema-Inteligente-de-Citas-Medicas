import { useState } from "react";
import { confirmAppointment } from "./appointmentService";
import { generateTicketPdf } from "../tickets/ticketPdfService";

function normalizarTicket(ticket = {}) {
  return {
    id: ticket.id,
    cita_id: ticket.cita_id ?? ticket.appointment_id,
    codigo: ticket.codigo ?? ticket.code,
    esta_confirmado: ticket.esta_confirmado ?? ticket.is_confirmed ?? false,
    emitido_en: ticket.emitido_en ?? ticket.issued_at,
  };
}

function toPdfTicket(ticket = {}) {
  const t = normalizarTicket(ticket);
  return {
    id: t.id,
    appointment_id: t.cita_id,
    code: t.codigo,
    is_confirmed: t.esta_confirmado,
    issued_at: t.emitido_en,
  };
}

function TicketConfirmForm() {
  const [appointmentId, setAppointmentId] = useState("");
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(false);

  const confirmar = async (e) => {
    e.preventDefault();

    if (!appointmentId.trim()) {
      alert("Ingrese el ID de la cita.");
      return;
    }

    try {
      setLoading(true);
      const response = await confirmAppointment(appointmentId);
      setTicket(normalizarTicket(response));
      alert(`Ticket generado: ${normalizarTicket(response).codigo}`);
      setAppointmentId("");
    } catch (error) {
      alert(JSON.stringify(error.response?.data || "Error desconocido", null, 2));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={confirmar} className="space-y-3">
      <input id="ticket-cita-id" type="number" value={appointmentId} onChange={(e) => setAppointmentId(e.target.value)} className="w-full border p-3 rounded-lg" placeholder="ID de la cita" min="1" required />

      <button type="submit" disabled={loading} className="w-full bg-blue-700 text-white p-3 rounded-lg">
        {loading ? "Confirmando..." : "Confirmar cita"}
      </button>

      {ticket && (
        <div className="mt-4 bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <h4 className="font-bold text-blue-900 mb-3">Ticket generado correctamente</h4>
          <p><strong>Código:</strong> {ticket.codigo}</p>
          <p><strong>Cita:</strong> {ticket.cita_id}</p>
          <p><strong>Confirmado:</strong> {ticket.esta_confirmado ? "Sí" : "No"}</p>
          <p><strong>Fecha de emisión:</strong> {ticket.emitido_en || "No disponible"}</p>

          <button type="button" onClick={async () => await generateTicketPdf(toPdfTicket(ticket))} className="mt-4 bg-purple-700 text-white px-4 py-2 rounded">
            Descargar PDF
          </button>
        </div>
      )}
    </form>
  );
}

export default TicketConfirmForm;
