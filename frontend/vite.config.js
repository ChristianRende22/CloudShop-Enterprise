import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// amazon-cognito-identity-js depende de "buffer", que a su vez espera el
// global "global" que Node define pero el navegador no. Vite (a diferencia
// de Webpack) no lo polyfillea solo -> "global is not defined" en runtime.
// (mismo fix ya aplicado en CloudBox Enterprise / Lab 7).
export default defineConfig({
  plugins: [react()],
  define: {
    global: "window",
  },
});
