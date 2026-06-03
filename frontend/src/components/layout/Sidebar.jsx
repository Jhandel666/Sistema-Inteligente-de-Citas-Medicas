import {
  Brain,
  CalendarDays,
  Hospital,
  LayoutDashboard,
  TicketCheck,
  UserRound,
  Users,
} from "lucide-react";

import MenuButton from "../ui/MenuButton";
import { getUserRole, isAdmin } from "../../modules/auth/sessionService";

function SidebarLabel({ text }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-widest text-blue-400 px-3 pt-4 pb-1 select-none">
      {text}
    </p>
  );
}

function Sidebar({ activePage, setActivePage }) {
  const role = getUserRole();

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-blue-900 text-white p-6">

      {/* Logo */}
      <div className="flex items-center gap-3 mb-8">
        <Hospital size={36} />
        <div>
          <h2 className="text-xl font-bold">MediGest IA</h2>
          <p className="text-sm text-blue-200">Sistema Inteligente de<br />Gestión de Citas Médicas</p>
        </div>
      </div>

      {/* Navegación */}
      <nav className="space-y-3">

        <SidebarLabel text="Principal" />

        <MenuButton
          active={activePage === "dashboard"}
          onClick={() => setActivePage("dashboard")}
          icon={<LayoutDashboard size={18} />}
          label="Dashboard"
        />

        <MenuButton
          active={activePage === "appointments"}
          onClick={() => setActivePage("appointments")}
          icon={<TicketCheck size={18} />}
          label="Citas Médicas"
        />

        <MenuButton
          active={activePage === "patients"}
          onClick={() => setActivePage("patients")}
          icon={<Users size={18} />}
          label="Pacientes"
        />

        {isAdmin() && (
          <MenuButton
            active={activePage === "doctors"}
            onClick={() => setActivePage("doctors")}
            icon={<UserRound size={18} />}
            label="Médicos"
          />
        )}

        <MenuButton
          active={activePage === "ai"}
          onClick={() => setActivePage("ai")}
          icon={<Brain size={18} />}
          label="IA / Voz"
        />

      </nav>

      {/* Footer */}
      <div className="absolute bottom-6 left-6 right-6 text-xs text-blue-200">
        <p>Rol activo:</p>
        <p className="font-bold uppercase">{role}</p>
      </div>
    </aside>
  );
}

export default Sidebar;
