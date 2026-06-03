import axios from "axios";

const api = axios.create({
  baseURL: "https://sistema-inteligente-de-citas-medicas.onrender.com/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

export default api;