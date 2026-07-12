import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="page">
      <h2>404</h2>
      <p>Esta página no existe.</p>
      <Link to="/productos">Volver</Link>
    </div>
  );
}
