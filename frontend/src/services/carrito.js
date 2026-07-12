import { api } from "./api";

export const listarCarrito = () => api.get("/carrito").then((r) => r.data);
export const agregarAlCarrito = (producto_id, cantidad = 1) =>
  api.post("/carrito", { producto_id, cantidad }).then((r) => r.data);
export const modificarCarrito = (productoId, cantidad) =>
  api.patch(`/carrito/${productoId}`, { cantidad }).then((r) => r.data);
export const eliminarDelCarrito = (productoId) => api.delete(`/carrito/${productoId}`).then((r) => r.data);
export const vaciarCarrito = () => api.delete("/carrito").then((r) => r.data);
