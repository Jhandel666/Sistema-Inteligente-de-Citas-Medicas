  import axios from "axios";

  const api = axios.create({
    baseURL: import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000/api/v1",
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

      if (error.response?.status === 401 && !originalRequest._retry) {
        const refreshToken = localStorage.getItem("refresh_token");

        if (!refreshToken) {
          localStorage.clear();
          window.location.reload();
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
          const baseURL = import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000/api/v1";
          const res = await axios.post(
            `${baseURL}/auth/refrescar`,
            { token_refresco: refreshToken, refresh_token: refreshToken },
          );

          const accessToken = res.data.token_acceso || res.data.access_token;
          const refreshTokenNuevo = res.data.token_refresco || res.data.refresh_token;

          localStorage.setItem("access_token", accessToken);
          localStorage.setItem("refresh_token", refreshTokenNuevo);

          pendingRequests.forEach((cb) => cb(accessToken));
          pendingRequests = [];

          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return api(originalRequest);
        } catch {
          localStorage.clear();
          window.location.reload();
          return Promise.reject(error);
        } finally {
          isRefreshing = false;
        }
      }

      return Promise.reject(error);
    },
  );

  export default api;
