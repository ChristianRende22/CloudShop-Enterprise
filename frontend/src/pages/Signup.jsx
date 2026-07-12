import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

// Nota académica: en producción el auto-registro solo debería permitir el
// rol "Cliente" (Administrador/Operador se provisionan vía Cognito admin).
// Aquí se deja elegible por rol para poder demostrar los 3 roles del RBAC
// sin depender de la consola/CLI de AWS — ver docs/documento-tecnico.
export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("Cliente");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signup(email, password, role);
      navigate("/confirmar", { state: { email } });
    } catch (err) {
      setError(err.message || "No se pudo registrar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>Crear cuenta</h1>
      <form onSubmit={onSubmit}>
        <label>Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
          <small>Mínimo 8 caracteres, con mayúscula, minúscula y número.</small>
        </label>
        <label>Rol
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="Cliente">Cliente</option>
            <option value="Operador">Operador</option>
            <option value="Administrador">Administrador</option>
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>{loading ? "Creando..." : "Registrarme"}</button>
      </form>
      <p className="hint">¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link></p>
    </div>
  );
}
