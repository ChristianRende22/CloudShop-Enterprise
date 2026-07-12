import { api } from "./api";

export const listarTiendas = () => api.get("/tiendas").then((r) => r.data);
export const obtenerTienda = (id) => api.get(`/tiendas/${id}`).then((r) => r.data);
export const crearTienda = (data) => api.post("/tiendas", data).then((r) => r.data);
export const actualizarTienda = (id, data) => api.patch(`/tiendas/${id}`, data).then((r) => r.data);
export const desactivarTienda = (id) => api.delete(`/tiendas/${id}`).then((r) => r.data);
