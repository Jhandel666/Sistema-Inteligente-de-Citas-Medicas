import api from "../../services/api";

export const getDashboardStats = async () => {
  const patientsResponse = await api.get("/patients/");
  const doctorsResponse = await api.get("/doctors/");
  const appointmentsResponse = await api.get("/appointments/");

  let ticketsCount = 0;

  try {
    const ticketsResponse = await api.get("/appointments/tickets/");
    ticketsCount = ticketsResponse.data.length;
  } catch (error) {
    console.warn("No se pudo cargar tickets:", error.response?.data || error);
    ticketsCount = 0;
  }

  return {
    patients: patientsResponse.data.length,
    doctors: doctorsResponse.data.length,
    appointments: appointmentsResponse.data.length,
    tickets: ticketsCount,
  };
};