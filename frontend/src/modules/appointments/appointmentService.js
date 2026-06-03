import api from "../../services/api";

async function intentar(fnPrincipal, fnAlternativa) {
  try {
    return await fnPrincipal();
  } catch (error) {
    if (error.response?.status === 404 && fnAlternativa) return await fnAlternativa();
    throw error;
  }
}

export const getAppointments = async () => {
  const response = await intentar(
    () => api.get("/appointments/"),
    () => api.get("/citas/"),
  );
  return response.data;
};

export const createAppointment = async (data) => {
  const response = await intentar(
    () => api.post("/appointments/", data),
    () => api.post("/citas/", data),
  );
  return response.data;
};

export const updateAppointment = async (id, data) => {
  const response = await intentar(
    () => api.put(`/appointments/${id}`, data),
    () => api.put(`/citas/${id}`, data),
  );
  return response.data;
};

export const deleteAppointment = async (id) => {
  const response = await intentar(
    () => api.delete(`/appointments/${id}`),
    () => api.delete(`/citas/${id}`),
  );
  return response.data;
};

export const confirmAppointment = async (appointmentId) => {
  const response = await intentar(
    () => api.post(`/appointments/${appointmentId}/confirmar`),
    () => api.post(`/appointments/${appointmentId}/confirm`),
  );
  return response.data;
};

export const cancelAppointment = async (appointmentId) => {
  const response = await intentar(
    () => api.post(`/appointments/${appointmentId}/cancelar`),
    () => api.post(`/appointments/${appointmentId}/cancel`),
  );
  return response.data;
};

export const predictAppointmentRisk = async (data) => {
  const response = await intentar(
    () => api.post("/appointments/predecir-riesgo", data),
    () => api.post("/appointments/predict-risk", data),
  );
  return response.data;
};

export const registerAttendance = async (citaId, data) => {
  const response = await api.post(`/appointments/${citaId}/asistencia`, data);
  return response.data;
};
