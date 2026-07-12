import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { RoleGate } from "../components/RoleGate";
import {
  listarProductos,
  crearProducto,
  actualizarProducto,
  eliminarProducto,
} from "../services/productos";
import { listarTiendas } from "../services/tiendas";
import { agregarAlCarrito } from "../services/carrito";

const VACIO = { codigo: "", nombre: "", descripcion: "", categoria: "", precio: "", inventario_disponible: "", tienda_id: "" };

export default function Productos() {
  const { user } = useAuth();
  const [productos, setProductos] = useState([]);
  const [tiendas, setTiendas] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [editandoId, setEditandoId] = useState(null);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    try {
      const [p, t] = await Promise.all([listarProductos(), listarTiendas()]);
      setProductos(p.items);
      setTiendas(t.items);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { cargar(); }, []);

  function nombreTienda(id) {
    return tiendas.find((t) => t.tienda_id === id)?.nombre || id;
  }

  async function onCrear(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      await crearProducto({
        ...form,
        precio: Number(form.precio),
        inventario_disponible: Number(form.inventario_disponible),
      });
      setForm(VACIO);
      setMsg("Producto creado.");
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onGuardarInventario(id, valor) {
    setError("");
    try {
      await actualizarProducto(id, { inventario_disponible: Number(valor) });
      setEditandoId(null);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onEliminar(id) {
    if (!confirm("¿Eliminar este producto definitivamente?")) return;
    setError("");
    try {
      await eliminarProducto(id);
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onAgregarCarrito(id) {
    setError(""); setMsg("");
    try {
      await agregarAlCarrito(id, 1);
      setMsg("Agregado al carrito.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h2>Productos</h2>
      {error && <p className="error">{error}</p>}
      {msg && <p className="ok">{msg}</p>}

      <RoleGate roles={["Administrador"]}>
        <details className="card">
          <summary>Crear producto</summary>
          <form onSubmit={onCrear} className="grid-form">
            <input placeholder="código" value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} required />
            <input placeholder="nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
            <input placeholder="categoría" value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} required />
            <input placeholder="precio" type="number" step="0.01" value={form.precio} onChange={(e) => setForm({ ...form, precio: e.target.value })} required />
            <input placeholder="inventario" type="number" value={form.inventario_disponible} onChange={(e) => setForm({ ...form, inventario_disponible: e.target.value })} required />
            <select value={form.tienda_id} onChange={(e) => setForm({ ...form, tienda_id: e.target.value })} required>
              <option value="">-- tienda --</option>
              {tiendas.map((t) => <option key={t.tienda_id} value={t.tienda_id}>{t.nombre}</option>)}
            </select>
            <input placeholder="descripción (opcional)" value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
            <button type="submit">Crear</button>
          </form>
        </details>
      </RoleGate>

      <table>
        <thead>
          <tr>
            <th>Código</th><th>Nombre</th><th>Categoría</th><th>Tienda</th><th>Precio</th><th>Inventario</th><th></th>
          </tr>
        </thead>
        <tbody>
          {productos.map((p) => (
            <tr key={p.producto_id}>
              <td>{p.codigo}</td>
              <td>{p.nombre}</td>
              <td>{p.categoria}</td>
              <td>{nombreTienda(p.tienda_id)}</td>
              <td>${Number(p.precio).toFixed(2)}</td>
              <td>
                <RoleGate roles={["Administrador", "Operador"]}>
                  {editandoId === p.producto_id ? (
                    <InventarioInline valor={p.inventario_disponible} onGuardar={(v) => onGuardarInventario(p.producto_id, v)} onCancelar={() => setEditandoId(null)} />
                  ) : (
                    <span onClick={() => setEditandoId(p.producto_id)} className="editable">{p.inventario_disponible}</span>
                  )}
                </RoleGate>
                <RoleGate roles={["Cliente"]}>{p.inventario_disponible}</RoleGate>
              </td>
              <td className="actions">
                <RoleGate roles={["Cliente"]}>
                  <button disabled={p.inventario_disponible <= 0} onClick={() => onAgregarCarrito(p.producto_id)}>
                    {p.inventario_disponible > 0 ? "Agregar" : "Agotado"}
                  </button>
                </RoleGate>
                <RoleGate roles={["Administrador"]}>
                  <button className="danger" onClick={() => onEliminar(p.producto_id)}>Eliminar</button>
                </RoleGate>
              </td>
            </tr>
          ))}
          {productos.length === 0 && <tr><td colSpan={7} className="hint">Sin productos todavía.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function InventarioInline({ valor, onGuardar, onCancelar }) {
  const [v, setV] = useState(valor);
  return (
    <span className="inline-edit">
      <input type="number" value={v} onChange={(e) => setV(e.target.value)} style={{ width: 70 }} />
      <button onClick={() => onGuardar(v)}>OK</button>
      <button onClick={onCancelar}>x</button>
    </span>
  );
}
