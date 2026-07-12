import { api } from "./api";

export const listarProductos = (tiendaId) =>
  api.get("/productos", { params: tiendaId ? { tienda_id: tiendaId } : {} }).then((r) => r.data);
export const obtenerProducto = (id) => api.get(`/productos/${id}`).then((r) => r.data);
export const crearProducto = (data) => api.post("/productos", data).then((r) => r.data);
export const actualizarProducto = (id, data) => api.patch(`/productos/${id}`, data).then((r) => r.data);
export const eliminarProducto = (id) => api.delete(`/productos/${id}`).then((r) => r.data);
