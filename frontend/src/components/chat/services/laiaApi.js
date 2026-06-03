import api from "../../../services/api";

export async function enviarChatIA(text) {
  const res = await api.post("/assistant/chat", { text });
  return res.data || {};
}

export async function obtenerEsquemaFormulario(entity) {
  const res = await api.get(`/assistant/form-schema/${entity}`);
  return res.data || {};
}

export async function enviarFormularioIA(entity, data) {
  const res = await api.post("/assistant/form-submit", { entity, data });
  return res.data || {};
}
