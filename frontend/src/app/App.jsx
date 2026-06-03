import { useState, useCallback } from "react";
import Sidebar from "../components/layout/Sidebar";
import LaIA from "../components/chat/LaIA";
import DashboardPage from "../pages/DashboardPage";
import PatientsPage from "../pages/PatientsPage";
import DoctorsPage from "../pages/DoctorsPage";
import AppointmentsPage from "../pages/AppointmentsPage";
import AiVoicePage from "../pages/AiVoicePage";
import LoginPage from "../pages/LoginPage";
import { isAuthenticated, logout } from "../modules/auth/authService";
import { FormFillingProvider } from "../context/FormFillingContext";

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [authenticated, setAuthenticated] = useState(isAuthenticated());
  const [pageKey, setPageKey] = useState(0);
  const [showLogin, setShowLogin] = useState(!isAuthenticated());

  const triggerRefresh = useCallback(() => setPageKey(k => k + 1), []);

  const renderPage = () => {
    if (activePage === "patients") return <PatientsPage key={`patients-${pageKey}`} />;
    if (activePage === "doctors") return <DoctorsPage key={`doctors-${pageKey}`} />;
    if (activePage === "appointments") return <AppointmentsPage key={`appointments-${pageKey}`} />;
    if (activePage === "ai") return <AiVoicePage key={`ai-${pageKey}`} />;
    return <DashboardPage key={`dashboard-${pageKey}`} />;
  };

  const cerrarSesion = () => {
    logout();
    setAuthenticated(false);
  };

  if (showLogin) {
    return <LoginPage onLoginSuccess={() => { setAuthenticated(true); setShowLogin(false); }} />;
  }

  return (
    <FormFillingProvider>
      <div className="min-h-screen bg-gray-100">
        <Sidebar activePage={activePage} setActivePage={setActivePage} />

        <main className="ml-72 p-8">
          <div className="flex items-start justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">
                Sistema Inteligente para la Gestión de Citas Médicas
              </h1>

              <p className="text-gray-600 mt-2">
                Hospital de Pichanaki — Autor: Jhandel Jesús Chavez Miranda
              </p>
            </div>

            {authenticated ? (
              <button onClick={cerrarSesion} className="bg-red-600 text-white px-5 py-3 rounded-lg">
                Cerrar sesión
              </button>
            ) : (
              <button onClick={() => setShowLogin(true)} className="bg-blue-600 text-white px-5 py-3 rounded-lg">
                Iniciar sesión
              </button>
            )}
          </div>

          {renderPage()}
        </main>
        <LaIA setActivePage={setActivePage} onAction={triggerRefresh} authenticated={authenticated} onLoginRequired={() => setShowLogin(true)} />
      </div>
    </FormFillingProvider>
  );
}

export default App;