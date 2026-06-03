import { useEffect, useState } from "react";

import PageCard from "../components/ui/PageCard";
import AppointmentForm from "../modules/appointments/AppointmentForm";
import AppointmentTable from "../modules/appointments/AppointmentTable";
import RiskResultModal from "../modules/appointments/RiskResultModal";

import { confirmAppointment, createAppointment, updateAppointment, deleteAppointment, getAppointments, predictAppointmentRisk, registerAttendance, } from "../modules/appointments/appointmentService";
import { exportAppointmentsCsv, exportAppointmentsPdf, } from "../modules/reports/appointmentReportService";

import { generateTicketPdf } from "../modules/tickets/ticketPdfService";

function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [lastTicket, setLastTicket] = useState(null);
  const [riskResult, setRiskResult] = useState(null);
  const [pendingData, setPendingData] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);

  const loadAppointments = async () => {
    try {
      const data = await getAppointments();
      setAppointments(data);
    } catch (error) {
      alert(JSON.stringify(error.response?.data || "Error al listar citas", null, 2));
    }
  };

  useEffect(() => {
    loadAppointments();
  }, []);

  const handlePredict = (data) => {
    setPendingData(data);
    setRiskResult(data.result);
  };

  const closeModal = () => {
    setRiskResult(null);
    setPendingData(null);
  };

  const predecirConIds = async (citaId) => {
    if (!pendingData) return;
    const payload = {
      ...pendingData.riskPayload,
      cita_id: citaId || null,
      paciente_id: pendingData.formData.paciente_id,
      medico_id: pendingData.formData.medico_id,
    };
    await predictAppointmentRisk(payload);
  };

  const handleCrear = async () => {
    if (!pendingData) return;
    setProcessing(true);
    try {
      const created = await createAppointment(pendingData.formData);
      await predecirConIds(created.id);
      alert("Cita creada correctamente");
      await loadAppointments();
    } catch (error) {
      alert(JSON.stringify(error.response?.data || "Error al crear cita", null, 2));
    } finally {
      setProcessing(false);
      closeModal();
    }
  };

  const handleConfirmarTicket = async () => {
    if (!pendingData) return;
    setProcessing(true);
    try {
      const created = await createAppointment(pendingData.formData);
      await predecirConIds(created.id);
      const ticket = await confirmAppointment(created.id);
      setLastTicket(ticket);
      alert(`Ticket generado: ${ticket.codigo}`);
      await loadAppointments();
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (error.response?.status === 409) {
        alert(typeof detail === "string" ? detail : "Esta cita ya tiene un ticket.");
      } else {
        alert(JSON.stringify(error.response?.data || "Error al crear cita + ticket", null, 2));
      }
    } finally {
      setProcessing(false);
      closeModal();
    }
  };

  const handlePendiente = async () => {
    if (!pendingData) return;
    setProcessing(true);
    try {
      const created = await createAppointment(pendingData.formData);
      await predecirConIds(created.id);
      alert("Cita creada como pendiente con predicción guardada");
      await loadAppointments();
    } catch (error) {
      alert(JSON.stringify(error.response?.data || "Error al crear cita pendiente", null, 2));
    } finally {
      setProcessing(false);
      closeModal();
    }
  };

  const handleDescartar = () => {
    setRiskResult(null);
    setPendingData(null);
  };

  const handleCancelEdit = () => {
    setEditingAppointment(null);
  };

  const handleConfirm = async (citaId) => {
    try {
      const ticket = await confirmAppointment(citaId);
      setLastTicket(ticket);
      alert(`Ticket generado: ${ticket.codigo}`);
      await loadAppointments();
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (error.response?.status === 409) {
        alert(typeof detail === "string" ? detail : "Esta cita ya tiene un ticket.");
      } else {
        alert(JSON.stringify(error.response?.data || "Error al confirmar cita", null, 2));
      }
    }
  };

  const handleEdit = (appointment) => {
    setEditingAppointment(appointment);
  };

  const handleDelete = async (citaId) => {
    if (!window.confirm("¿Está seguro de eliminar esta cita?")) return;
    try {
      await deleteAppointment(citaId);
      alert("Cita eliminada correctamente");
      await loadAppointments();
    } catch (error) {
      alert(JSON.stringify(error.response?.data || "Error al eliminar cita", null, 2));
    }
  };

  const handleAttendance = async (citaId, asistio) => {
    try {
      const cita = appointments.find((a) => a.id === citaId);
      if (!cita) return;
      const pacienteId = cita.paciente_id ?? cita.patient_id ?? cita.paciente?.id;
      if (!pacienteId) {
        alert("No se pudo determinar el paciente de esta cita.");
        return;
      }
      await registerAttendance(citaId, { paciente_id: pacienteId, cita_id: citaId, asistio });
      alert(asistio ? "Asistencia registrada correctamente." : "Inasistencia registrada correctamente.");
      loadAppointments();
    } catch (error) {
      alert(JSON.stringify(error.response?.data || "Error al registrar asistencia", null, 2));
    }
  };

  return (
    <div>
      <PageCard title={editingAppointment ? `Editando cita #${editingAppointment.id}` : "Crear Cita Médica con Predicción IA"}>
        <AppointmentForm onPredict={handlePredict} initialData={editingAppointment} onCancelEdit={handleCancelEdit} />
      </PageCard>

      <PageCard title="Listado de Citas" fullWidth>
        <div className="flex gap-3 mb-4">
          <button type="button" onClick={() => exportAppointmentsPdf(appointments)} className="bg-purple-700 text-white px-4 py-2 rounded">
            Exportar PDF
          </button>
          <button type="button" onClick={() => exportAppointmentsCsv(appointments)} className="bg-green-700 text-white px-4 py-2 rounded">
            Exportar CSV
          </button>
        </div>
        <AppointmentTable
          appointments={appointments}
          onConfirm={handleConfirm}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onAttendance={handleAttendance}
        />
      </PageCard>

      {lastTicket && (
        <PageCard title="Último Ticket Generado">
          <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
            <p><strong>Código:</strong> {lastTicket.codigo || lastTicket.code}</p>
            <p><strong>ID de cita:</strong> {lastTicket.cita_id || lastTicket.appointment_id}</p>
            <p><strong>Confirmado:</strong> {(lastTicket.esta_confirmado ?? lastTicket.is_confirmed) ? "Sí" : "No"}</p>
            <p><strong>Fecha de emisión:</strong> {lastTicket.emitido_en || lastTicket.issued_at || "No disponible"}</p>
            <button type="button" onClick={async () => await generateTicketPdf(lastTicket)} className="mt-4 bg-purple-700 text-white px-4 py-2 rounded">
              Descargar PDF con QR
            </button>
          </div>
        </PageCard>
      )}

      {riskResult && (
        <RiskResultModal
          result={riskResult}
          onCrear={pendingData?.isEditing ? handleGuardarCambios : handleCrear}
          onConfirmarTicket={handleConfirmarTicket}
          onPendiente={handlePendiente}
          onDescartar={handleDescartar}
          editMode={pendingData?.isEditing}
        />
      )}

      {processing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white p-6 rounded-xl shadow-xl text-lg font-semibold">Procesando...</div>
        </div>
      )}
    </div>
  );
}

export default AppointmentsPage;