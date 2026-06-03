import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export const exportPatientsPdf = (patients) => {
  const doc = new jsPDF();

  doc.setFontSize(18);
  doc.text("Hospital de Pichanaki", 14, 18);

  doc.setFontSize(13);
  doc.text("Reporte de Pacientes", 14, 28);

  autoTable(doc, {
    startY: 38,
    head: [["ID", "Paciente", "DNI", "Correo", "Teléfono"]],
    body: patients.map((p) => [
      p.id,
      `${p.first_name} ${p.last_name}`,
      p.document_number,
      p.email,
      p.phone,
    ]),
  });

  doc.save("reporte-pacientes.pdf");
};

export const exportPatientsCsv = (patients) => {
  const headers = ["ID", "Paciente", "DNI", "Correo", "Telefono"];

  const rows = patients.map((p) => [
    p.id,
    `${p.first_name} ${p.last_name}`,
    p.document_number,
    p.email,
    p.phone,
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
  link.download = "reporte-pacientes.csv";
  link.click();

  URL.revokeObjectURL(url);
};