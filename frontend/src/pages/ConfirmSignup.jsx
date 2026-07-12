import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function ConfirmSignup() {
  const { confirm } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState(location.state?.email || "");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await confirm(email, code);
      setOk(true);
    } catch (err) {
      setError(err.message || "Código inválido");
    } finally {
      setLoading(false);
    }
  }

  if (ok) {
    return (
      <div className="auth-card">
        <h1>Cuenta confirmada</h1>
        <p className="hint">Ya puedes iniciar sesión.</p>
        <Link to="/login"><button>Ir a login</button></Link>
      </div>
    );
  }

  return (
    <div className="auth-card">
      <h1>Confirmar cuenta</h1>
      <p className="hint">Revisa tu correo, Cognito te envió un código de verificación.</p>
      <form onSubmit={onSubmit}>
        <label>Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>Código
          <input value={code} onChange={(e) => setCode(e.target.value)} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>{loading ? "Confirmando..." : "Confirmar"}</button>
      </form>
    </div>
  );
}
