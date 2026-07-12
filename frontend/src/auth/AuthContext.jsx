import { createContext, useContext, useEffect, useState, useCallback } from "react";
import * as cognito from "./cognito";
import { crearPerfil } from "../services/usuarios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { sub, email, role }
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const session = await cognito.getSession();
    setUser(cognito.claimsFromSession(session));
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  async function login(email, password) {
    await cognito.signIn(email, password);
    await refresh();
    await asegurarPerfil(email.split("@")[0]);
  }

  async function signup(email, password, role) {
    await cognito.signUp(email, password, role);
  }

  async function confirm(email, code) {
    await cognito.confirmSignUp(email, code);
  }

  /**
   * Se llama justo despues del primer login post-confirmacion. Crea el
   * perfil de aplicacion en la tabla Usuarios (Modulo 1). El backend
   * (usuarios.handler.crear) solo permite auto-asignarse un rol distinto de
   * "Cliente" si el JWT YA trae ese rol (es_admin viene del token, no del
   * body) — por eso esto es best-effort: si el backend lo rechaza (409 ya
   * existe, o 403 en un caso borde de Operador auto-registrado) no bloquea
   * el login, la autorizacion real de cada endpoint siempre se valida con
   * el claim custom:role del token, no con este perfil informativo.
   */
  async function asegurarPerfil(nombre) {
    const session = await cognito.getSession();
    const claims = cognito.claimsFromSession(session);
    if (!claims) return;
    try {
      await crearPerfil({ nombre, email: claims.email, rol: claims.role });
    } catch (_e) {
      // no-op: perfil ya existe o el backend restringio el rol autodeclarado
    }
  }

  function logout() {
    cognito.signOut();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, confirm, asegurarPerfil, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
