import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export const exportDoctorsPdf = (doctors) => {
  const doc = new jsPDF();

  doc.setFontSize(18);
  doc.text("Hospital de Pichanaki", 14, 18);

  doc.setFontSize(13);
  doc.text("Reporte de Médicos", 14, 28);

  autoTable(doc, {
    startY: 38,
    head: [["ID", "Médico", "Especialidad", "Correo"]],
    body: doctors.map((d) => [
      d.id,
      `${d.first_name} ${d.last_name}`,
      d.specialty,
      d.email,
    ]),
  });

  doc.save("reporte-medicos.pdf");
};

export const exportDoctorsCsv = (doctors) => {
  const headers = ["ID", "Medico", "Especialidad", "Correo"];

  const rows = doctors.map((d) => [
    d.id,
    `${d.first_name} ${d.last_name}`,
    d.specialty,
    d.email,
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
  link.download = "reporte-medicos.csv";
  link.click();

  URL.revokeObjectURL(url);
};