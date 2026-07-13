import { useEffect, useState } from "react";
import { obtenerDashboard } from "../services/dashboard";
import { listarTiendas } from "../services/tiendas";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [tiendasPorId, setTiendasPorId] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([obtenerDashboard(), listarTiendas()])
      .then(([dash, tiendas]) => {
        setData(dash);
        setTiendasPorId(Object.fromEntries(tiendas.items.map((t) => [t.tienda_id, t.nombre])));
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="hint">Cargando dashboard...</p>;

  return (
    <div className="page">
      <h2>Dashboard ejecutivo</h2>

      <div className="stats-grid">
        <div className="stat"><span className="stat-label">Ventas totales</span><span className="stat-value">${Number(data.total_ventas).toFixed(2)}</span></div>
        {Object.entries(data.pedidos_por_estado).map(([estado, n]) => (
          <div className="stat" key={estado}><span className="stat-label">{estado}</span><span className="stat-value">{n}</span></div>
        ))}
      </div>

      <div className="dash-cols">
        <div>
          <h3>Ventas por tienda</h3>
          <table>
            <thead><tr><th>Tienda</th><th>Total</th></tr></thead>
            <tbody>
              {data.ventas_por_tienda.map((v) => (
                <tr key={v.tienda_id}><td>{tiendasPorId[v.tienda_id] || v.tienda_id}</td><td>${Number(v.total).toFixed(2)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h3>Más vendidos</h3>
          <table>
            <thead><tr><th>Producto</th><th>Unidades</th></tr></thead>
            <tbody>
              {data.productos_mas_vendidos.map((p) => <tr key={p.producto_id}><td>{p.nombre}</td><td>{p.unidades_vendidas}</td></tr>)}
            </tbody>
          </table>
        </div>
        <div>
          <h3>Clientes top</h3>
          <table>
            <thead><tr><th>Cliente</th><th>Comprado</th></tr></thead>
            <tbody>
              {data.clientes_top.map((c) => <tr key={c.cliente_id}><td>{c.cliente_email}</td><td>${Number(c.total_comprado).toFixed(2)}</td></tr>)}
            </tbody>
          </table>
        </div>
        <div>
          <h3>Productos agotados</h3>
          {data.productos_agotados.length === 0 ? <p className="hint">Ninguno.</p> : (
            <ul>{data.productos_agotados.map((p) => <li key={p.producto_id}>{p.nombre}</li>)}</ul>
          )}
        </div>
      </div>
    </div>
  );
}
