import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listarCarrito, modificarCarrito, eliminarDelCarrito, vaciarCarrito } from "../services/carrito";
import { crearPedido } from "../services/pedidos";
import { listarProductos } from "../services/productos";

export default function Carrito() {
  const [items, setItems] = useState([]);
  const [productosPorId, setProductosPorId] = useState({});
  const [error, setError] = useState("");
  const [creando, setCreando] = useState(false);
  const navigate = useNavigate();

  async function cargar() {
    try {
      const [c, p] = await Promise.all([listarCarrito(), listarProductos()]);
      setItems(c.items);
      setProductosPorId(Object.fromEntries(p.items.map((x) => [x.producto_id, x])));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { cargar(); }, []);

  async function onCantidad(productoId, cantidad) {
    setError("");
    try {
      if (cantidad <= 0) return;
      await modificarCarrito(productoId, Number(cantidad));
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onEliminar(productoId) {
    setError("");
    try {
      await eliminarDelCarrito(productoId);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onVaciar() {
    setError("");
    try {
      await vaciarCarrito();
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onCheckout() {
    setError("");
    setCreando(true);
    try {
      const items_pedido = items.map((i) => ({ producto_id: i.producto_id, cantidad: Number(i.cantidad) }));
      const pedido = await crearPedido(items_pedido);
      await vaciarCarrito();
      navigate("/pedidos", { state: { creado: pedido.pedido_id } });
    } catch (err) {
      setError(err.message);
    } finally {
      setCreando(false);
    }
  }

  const total = items.reduce((acc, i) => {
    const p = productosPorId[i.producto_id];
    return acc + (p ? Number(p.precio) * Number(i.cantidad) : 0);
  }, 0);

  return (
    <div className="page">
      <h2>Mi carrito</h2>
      {error && <p className="error">{error}</p>}

      <table>
        <thead><tr><th>Producto</th><th>Precio</th><th>Cantidad</th><th>Subtotal</th><th></th></tr></thead>
        <tbody>
          {items.map((i) => {
            const p = productosPorId[i.producto_id];
            const subtotal = p ? Number(p.precio) * Number(i.cantidad) : 0;
            return (
              <tr key={i.producto_id}>
                <td>{p ? p.nombre : i.producto_id}</td>
                <td>{p ? `$${Number(p.precio).toFixed(2)}` : "—"}</td>
                <td>
                  <input
                    type="number"
                    min={1}
                    value={i.cantidad}
                    style={{ width: 70 }}
                    onChange={(e) => onCantidad(i.producto_id, e.target.value)}
                  />
                </td>
                <td>${subtotal.toFixed(2)}</td>
                <td><button className="danger" onClick={() => onEliminar(i.producto_id)}>Quitar</button></td>
              </tr>
            );
          })}
          {items.length === 0 && <tr><td colSpan={5} className="hint">Tu carrito está vacío.</td></tr>}
        </tbody>
      </table>

      {items.length > 0 && (
        <div className="actions" style={{ marginTop: 16, alignItems: "center" }}>
          <strong>Total: ${total.toFixed(2)}</strong>
          <button onClick={onVaciar}>Vaciar carrito</button>
          <button onClick={onCheckout} disabled={creando}>{creando ? "Creando pedido..." : "Confirmar pedido"}</button>
        </div>
      )}
    </div>
  );
}
