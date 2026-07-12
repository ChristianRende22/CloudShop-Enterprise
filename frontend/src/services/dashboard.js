import { api } from "./api";

export const obtenerDashboard = () => api.get("/dashboard").then((r) => r.data);
