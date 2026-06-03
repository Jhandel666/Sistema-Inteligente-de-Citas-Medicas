import api from "../../services/api";

export const classifyIntent = async (text) => {
  const response = await api.post("/appointments/voz/intencion", { text });
  return response.data;
};