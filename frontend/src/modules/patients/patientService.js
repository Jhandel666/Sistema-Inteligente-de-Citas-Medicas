import api from "../../services/api";

const rutas = {
  principal: "/patients/",
  alternativa: "/pacientes/",
};

async function intentar(fnPrincipal, fnAlternativa) {
  try {
    return await fnPrincipal();
  } catch (error) {
    if (error.response?.status === 404 && fnAlternativa) return await fnAlternativa();
    throw error;
  }
}

export const getPatients = async () => {
  const response = await intentar(
    () => api.get(rutas.principal),
    () => api.get(rutas.alternativa),
  );
  return response.data;
};

export const createPatient = async (data) => {
  const response = await intentar(
    () => api.post(rutas.principal, data),
    () => api.post(rutas.alternativa, data),
  );
  return response.data;
};

export const updatePatient = async (id, data) => {
  const response = await intentar(
    () => api.put(`/patients/${id}`, data),
    () => api.put(`/pacientes/${id}`, data),
  );
  return response.data;
};

export const deletePatient = async (id) => {
  const response = await intentar(
    () => api.delete(`/patients/${id}`),
    () => api.delete(`/pacientes/${id}`),
  );
  return response.data;
};
