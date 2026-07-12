import { api } from "./api";

export const crearPerfil = (data) => api.post("/usuarios", data).then((r) => r.data);
export const listarUsuarios = (limit = 50) => api.get(`/usuarios?limit=${limit}`).then((r) => r.data);
export const obtenerUsuario = (id) => api.get(`/usuarios/${id}`).then((r) => r.data);
export const actualizarUsuario = (id, data) => api.patch(`/usuarios/${id}`, data).then((r) => r.data);
export const desactivarUsuario = (id) => api.delete(`/usuarios/${id}`).then((r) => r.data);
