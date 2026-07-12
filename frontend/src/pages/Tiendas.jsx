import { useEffect, useState } from "react";
import { RoleGate } from "../components/RoleGate";
import { listarTiendas, crearTienda, actualizarTienda, desactivarTienda } from "../services/tiendas";

export default function Tiendas() {
  const [tiendas, setTiendas] = useState([]);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  async function cargar() {
    try {
      const r = await listarTiendas();
      setTiendas(r.items);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { cargar(); }, []);

  async function onCrear(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      await crearTienda({ nombre, descripcion });
      setNombre(""); setDescripcion("");
      setMsg("Tienda creada.");
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onToggleEstado(t) {
    setError("");
    try {
      if (t.estado === "ACTIVA") {
        await desactivarTienda(t.tienda_id);
      } else {
        await actualizarTienda(t.tienda_id, { estado: "ACTIVA" });
      }
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h2>Tiendas</h2>
      {error && <p className="error">{error}</p>}
      {msg && <p className="ok">{msg}</p>}

      <RoleGate roles={["Administrador"]}>
        <details className="card">
          <summary>Crear tienda</summary>
          <form onSubmit={onCrear} className="grid-form">
            <input placeholder="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
            <input placeholder="descripción" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
            <button type="submit">Crear</button>
          </form>
        </details>
      </RoleGate>

      <table>
        <thead><tr><th>Nombre</th><th>Descripción</th><th>Estado</th><th></th></tr></thead>
        <tbody>
          {tiendas.map((t) => (
            <tr key={t.tienda_id}>
              <td>{t.nombre}</td>
              <td>{t.descripcion}</td>
              <td><span className={`badge ${t.estado === "ACTIVA" ? "badge-ok" : "badge-off"}`}>{t.estado}</span></td>
              <td>
                <RoleGate roles={["Administrador"]}>
                  <button onClick={() => onToggleEstado(t)}>
                    {t.estado === "ACTIVA" ? "Desactivar" : "Reactivar"}
                  </button>
                </RoleGate>
              </td>
            </tr>
          ))}
          {tiendas.length === 0 && <tr><td colSpan={4} className="hint">Sin tiendas todavía.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
