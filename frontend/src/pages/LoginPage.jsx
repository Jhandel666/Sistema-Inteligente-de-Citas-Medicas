import { useState } from "react";
import { Hospital, Lock } from "lucide-react";
import { login, saveSession } from "../modules/auth/authService";

function LoginPage({ onLoginSuccess }) {
  const [credentials, setCredentials] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value,
    });
  };

  const ingresar = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);

      const tokenData = await login(credentials);
      saveSession(tokenData);

      onLoginSuccess();
    } catch (error) {
      alert(
        JSON.stringify(
          error.response?.data || "Credenciales incorrectas",
          null,
          2
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-blue-950 flex items-center justify-center px-4">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-blue-900 text-white p-4 rounded-full mb-4">
            <Hospital size={42} />
          </div>

          <h1 className="text-2xl font-bold text-gray-800 text-center">
            Hospital de Pichanaki
          </h1>

          <p className="text-gray-500 text-center mt-2">
            Sistema Inteligente de Gestión de Citas Médicas
          </p>
        </div>

        <form onSubmit={ingresar} className="space-y-4">
          <input
            type="email"
            name="email"
            value={credentials.email}
            onChange={handleChange}
            className="w-full border p-3 rounded-lg"
            placeholder="Correo institucional"
          />

          <input
            type="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            className="w-full border p-3 rounded-lg"
            placeholder="Contraseña"
          />

          <button
            disabled={loading}
            className="w-full bg-blue-900 text-white p-3 rounded-lg flex items-center justify-center gap-2"
          >
            <Lock size={18} />
            {loading ? "Ingresando..." : "Ingresar al sistema"}
          </button>
        </form>

        <p className="text-xs text-gray-400 text-center mt-6">
          Autor: Jhandel Jesús Chavez Miranda
        </p>
      </div>
    </div>
  );
}

export default LoginPage;