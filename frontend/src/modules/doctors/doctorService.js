import api from "../../services/api";

async function intentar(fnPrincipal, fnAlternativa) {
  try {
    return await fnPrincipal();
  } catch (error) {
    if (error.response?.status === 404 && fnAlternativa) return await fnAlternativa();
    throw error;
  }
}

export const getDoctors = async () => {
  const response = await intentar(
    () => api.get("/doctors/"),
    () => api.get("/medicos/"),
  );
  return response.data;
};

export const createDoctor = async (data) => {
  const response = await intentar(
    () => api.post("/doctors/", data),
    () => api.post("/medicos/", data),
  );
  return response.data;
};

export const updateDoctor = async (id, data) => {
  const response = await intentar(
    () => api.put(`/doctors/${id}`, data),
    () => api.put(`/medicos/${id}`, data),
  );
  return response.data;
};

export const deleteDoctor = async (id) => {
  const response = await intentar(
    () => api.delete(`/doctors/${id}`),
    () => api.delete(`/medicos/${id}`),
  );
  return response.data;
};
