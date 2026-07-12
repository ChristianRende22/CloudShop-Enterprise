import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Navbar } from "./components/Navbar";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ConfirmSignup from "./pages/ConfirmSignup";
import Productos from "./pages/Productos";
import Tiendas from "./pages/Tiendas";
import Carrito from "./pages/Carrito";
import Pedidos from "./pages/Pedidos";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <AuthProvider>
      <Navbar />
      <Routes>
        <Route path="/" element={<Navigate to="/productos" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/confirmar" element={<ConfirmSignup />} />

        <Route path="/productos" element={<ProtectedRoute><Productos /></ProtectedRoute>} />
        <Route path="/tiendas" element={<ProtectedRoute><Tiendas /></ProtectedRoute>} />
        <Route path="/carrito" element={<ProtectedRoute roles={["Cliente"]}><Carrito /></ProtectedRoute>} />
        <Route path="/pedidos" element={<ProtectedRoute><Pedidos /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute roles={["Administrador"]}><Dashboard /></ProtectedRoute>} />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}
