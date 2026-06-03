import axios from "axios";

// URL fija de producción para evitar errores de Vercel con variables de entorno.
const API_BASE_URL = "https://sistema-inteligente-de-citas-medicas.onrender.com/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

let isRefreshing = false;
let pendingRequests = [];

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        localStorage.clear();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const res = await axios.post(
          `${API_BASE_URL}/auth/refrescar`,
          { token_refresco: refreshToken, refresh_token: refreshToken },
          { headers: { "Content-Type": "application/json" } },
        );

        const accessToken = res.data.token_acceso || res.data.access_token;
        const refreshTokenNuevo = res.data.token_refresco || res.data.refresh_token;

        if (accessToken) localStorage.setItem("access_token", accessToken);
        if (refreshTokenNuevo) localStorage.setItem("refresh_token", refreshTokenNuevo);

        pendingRequests.forEach((cb) => cb(accessToken));
        pendingRequests = [];

        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.clear();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export default api;
