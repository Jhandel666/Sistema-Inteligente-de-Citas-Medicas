import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export const exportAppointmentsPdf = (appointments) => {
  const doc = new jsPDF();

  doc.setFontSize(18);
  doc.text("Hospital de Pichanaki", 14, 18);

  doc.setFontSize(13);
  doc.text("Reporte de Citas Médicas", 14, 28);

  autoTable(doc, {
    startY: 38,
    head: [["ID", "Paciente ID", "Médico ID", "Fecha", "Estado", "Motivo"]],
    body: appointments.map((a) => [
      a.id,
      a.paciente_id ?? a.patient_id,
      a.medico_id ?? a.doctor_id,
      a.programada_en ?? a.scheduled_at,
      a.estado ?? a.status,
      a.motivo ?? a.reason,
    ]),
  });

  doc.save("reporte-citas.pdf");
};

export const exportAppointmentsCsv = (appointments) => {
  const headers = ["ID", "Paciente ID", "Medico ID", "Fecha", "Estado", "Motivo"];

  const rows = appointments.map((a) => [
    a.id,
    a.paciente_id ?? a.patient_id,
    a.medico_id ?? a.doctor_id,
    a.programada_en ?? a.scheduled_at,
    a.estado ?? a.status,
    a.motivo ?? a.reason,
  ]);

  const csvContent = [headers, ...rows]
    .map((row) => row.map((value) => `"${value ?? ""}"`).join(","))
    .join("\n");

  const blob = new Blob([csvContent], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "reporte-citas.csv";
  link.click();

  URL.revokeObjectURL(url);
};