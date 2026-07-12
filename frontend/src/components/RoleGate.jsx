import { useAuth } from "../auth/AuthContext";

/** Muestra los hijos solo si el rol actual está en `roles`. */
export function RoleGate({ roles, children }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) return null;
  return children;
}
