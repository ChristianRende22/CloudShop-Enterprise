import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { RoleGate } from "../components/RoleGate";
import { listarPedidos, avanzarEstadoPedido, cancelarPedido } from "../services/pedidos";

const ESTADOS_ORDEN = ["Pendiente", "Confirmado", "En preparación", "Enviado", "Entregado"];
const CANCELABLES = ["Pendiente", "Confirmado", "En preparación"];

export default function Pedidos() {
  const { user } = useAuth();
  const location = useLocation();
  const [pedidos, setPedidos] = useState([]);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState(location.state?.creado ? `Pedido ${location.state.creado} creado.` : "");

  async function cargar() {
    try {
      const r = await listarPedidos();
      setPedidos(r.items.sort((a, b) => (a.fecha_creacion < b.fecha_creacion ? 1 : -1)));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { cargar(); }, []);

  function siguienteEstado(estado) {
    const i = ESTADOS_ORDEN.indexOf(estado);
    return i >= 0 && i < ESTADOS_ORDEN.length - 1 ? ESTADOS_ORDEN[i + 1] : null;
  }

  async function onAvanzar(id, estadoActual) {
    const siguiente = siguienteEstado(estadoActual);
    if (!siguiente) return;
    setError("");
    try {
      await avanzarEstadoPedido(id, siguiente);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onCancelar(id) {
    if (!confirm("¿Cancelar este pedido? Se devuelve el inventario reservado.")) return;
    setError("");
    try {
      await cancelarPedido(id);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h2>{user.role === "Cliente" ? "Mis pedidos" : "Pedidos"}</h2>
      {error && <p className="error">{error}</p>}
      {msg && <p className="ok">{msg}</p>}

      {pedidos.map((p) => (
        <div key={p.pedido_id} className="card">
          <div className="pedido-header">
            <strong>#{p.pedido_id.slice(0, 8)}</strong>
            <span className={`badge ${p.estado === "Cancelado" ? "badge-off" : "badge-ok"}`}>{p.estado}</span>
            <span>Total: ${Number(p.total).toFixed(2)}</span>
            <span className="hint">{p.fecha_creacion}</span>
          </div>
          <ul>
            {p.items.map((it) => (
              <li key={it.producto_id}>{it.cantidad} x {it.nombre} — ${Number(it.subtotal).toFixed(2)}</li>
            ))}
          </ul>
          <div className="actions">
            <RoleGate roles={["Administrador", "Operador"]}>
              {siguienteEstado(p.estado) && (
                <button onClick={() => onAvanzar(p.pedido_id, p.estado)}>
                  Avanzar a "{siguienteEstado(p.estado)}"
                </button>
              )}
            </RoleGate>
            {CANCELABLES.includes(p.estado) && (
              <button className="danger" onClick={() => onCancelar(p.pedido_id)}>Cancelar</button>
            )}
          </div>
        </div>
      ))}
      {pedidos.length === 0 && <p className="hint">Sin pedidos todavía.</p>}
    </div>
  );
}
