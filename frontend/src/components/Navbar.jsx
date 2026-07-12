import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Navbar() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <nav className="navbar">
      <span className="brand">CloudShop</span>
      <NavLink to="/productos">Productos</NavLink>
      <NavLink to="/tiendas">Tiendas</NavLink>
      {user.role === "Cliente" && <NavLink to="/carrito">Carrito</NavLink>}
      <NavLink to="/pedidos">Pedidos</NavLink>
      {user.role === "Administrador" && <NavLink to="/dashboard">Dashboard</NavLink>}
      <span className="spacer" />
      <span className="who">{user.email} · {user.role}</span>
      <button onClick={logout}>Salir</button>
    </nav>
  );
}
