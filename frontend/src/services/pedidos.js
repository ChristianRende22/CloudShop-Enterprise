import { api } from "./api";

export const crearPedido = (items) => api.post("/pedidos", { items }).then((r) => r.data);
export const listarPedidos = (clienteId) =>
  api.get("/pedidos", { params: clienteId ? { cliente_id: clienteId } : {} }).then((r) => r.data);
export const obtenerPedido = (id) => api.get(`/pedidos/${id}`).then((r) => r.data);
export const avanzarEstadoPedido = (id, estado) => api.patch(`/pedidos/${id}`, { estado }).then((r) => r.data);
export const cancelarPedido = (id) => api.delete(`/pedidos/${id}`).then((r) => r.data);
