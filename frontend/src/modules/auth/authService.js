import api from "../../services/api";

export const login = async (credentials) => {
  const payload = {
    correo: credentials.correo || credentials.email || credentials.username || "",
    email: credentials.correo || credentials.email || credentials.username || "",
    contrasena: credentials.contrasena || credentials.password || credentials.clave || "",
    password: credentials.contrasena || credentials.password || credentials.clave || "",
  };

  const response = await api.post("/auth/ingresar", payload);
  return response.data;
};

export const registerUser = async (data) => {
  const payload = {
    nombre_completo: data.nombre_completo || data.full_name || data.name,
    correo: data.correo || data.email,
    contrasena: data.contrasena || data.password,
    rol: data.rol || data.role || "recepcion",
  };

  const response = await api.post("/auth/registrar", payload);
  return response.data;
};

export const saveSession = (tokenData) => {
  const tokenAcceso = tokenData.token_acceso || tokenData.access_token;
  const tokenRefresco = tokenData.token_refresco || tokenData.refresh_token;

  if (tokenAcceso) localStorage.setItem("access_token", tokenAcceso);
  if (tokenRefresco) localStorage.setItem("refresh_token", tokenRefresco);
};

export const getAccessToken = () => {
  return localStorage.getItem("access_token");
};

export const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

export const isAuthenticated = () => {
  return Boolean(getAccessToken());
};
