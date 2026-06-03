import jsPDF from "jspdf";
import QRCode from "qrcode";

export const generateTicketPdf = async (ticket) => {
  const doc = new jsPDF();

  const qrText = `Ticket: ${ticket.codigo || ticket.code} | Cita: ${ticket.cita_id || ticket.appointment_id}`;
  const qrImage = await QRCode.toDataURL(qrText);

  doc.setFontSize(18);
  doc.text("Hospital de Pichanaki", 20, 20);

  doc.setFontSize(14);
  doc.text("Ticket de Cita Médica", 20, 35);

  doc.setFontSize(11);
  doc.text(`Código de Ticket: ${ticket.codigo || ticket.code}`, 20, 55);
  doc.text(`ID de Cita: ${ticket.cita_id || ticket.appointment_id}`, 20, 70);
  doc.text(`Confirmado: ${(ticket.esta_confirmado ?? ticket.is_confirmed) ? "Sí" : "No"}`, 20, 85);
  doc.text(`Fecha de emisión: ${ticket.emitido_en || ticket.issued_at || "No disponible"}`, 20, 100);

  doc.addImage(qrImage, "PNG", 130, 45, 50, 50);

  doc.text("Sistema Inteligente para la Gestión de Citas Médicas", 20, 125);
  doc.text("Autor: Jhandel Jesús Chavez Miranda", 20, 140);

  doc.save(`ticket-${ticket.codigo || ticket.code}.pdf`);
};