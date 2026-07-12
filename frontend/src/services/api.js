import axios from "axios";
import { getIdToken } from "../auth/cognito";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// El backend valida el rol SIEMPRE server-side (common.auth.require_roles);
// este header es solo lo que exige el Cognito Authorizer de API Gateway
// (Clase 16) para dejar pasar la request antes de invocar el Lambda.
api.interceptors.request.use(async (config) => {
  const token = await getIdToken();
  if (token) config.headers.Authorization = token;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.error || err.message || "Error de red";
    return Promise.reject(new Error(msg));
  }
);
