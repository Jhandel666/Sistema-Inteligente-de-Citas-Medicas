import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

import StatCard from "../components/ui/StatCard";
import api from "../services/api";

function DashboardPage() {
  const [stats, setStats] = useState({
    patients: 0,
    doctors: 0,
    appointments: 0,
    tickets: 0,
    pending: 0,
    confirmed: 0,
    cancelled: 0,
  });

  const [appointments, setAppointments] = useState([]);

  const loadDashboard = async () => {
    try {
      const [patientsRes, doctorsRes, appointmentsRes, ticketsRes] =
        await Promise.all([
          api.get("/patients/"),
          api.get("/doctors/"),
          api.get("/appointments/"),
          api.get("/appointments/tickets/"),
        ]);

      const appointmentsData = appointmentsRes.data;

      setStats({
        patients: patientsRes.data.length,
        doctors: doctorsRes.data.length,
        appointments: appointmentsData.length,
        tickets: ticketsRes.data.length,
        pending: appointmentsData.filter((a) => (a.estado || a.status) === "pendiente").length,
        confirmed: appointmentsData.filter((a) => (a.estado || a.status) === "confirmada").length,
        cancelled: appointmentsData.filter((a) => (a.estado || a.status) === "cancelada").length,
      });

      setAppointments(appointmentsData.slice(0, 5));
    } catch (error) {
      alert(
        JSON.stringify(
          error.response?.data || error.message || "Error cargando dashboard",
          null,
          2
        )
      );
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const chartData = [
    { name: "Pendientes", value: stats.pending },
    { name: "Confirmadas", value: stats.confirmed },
    { name: "Canceladas", value: stats.cancelled },
  ];

  return (
    <div className="space-y-8 mt-8">
      <section className="grid grid-cols-4 gap-6">
        <StatCard title="Pacientes" value={stats.patients} />
        <StatCard title="Médicos" value={stats.doctors} />
        <StatCard title="Citas" value={stats.appointments} />
        <StatCard title="Tickets" value={stats.tickets} />
      </section>

      <section className="grid grid-cols-3 gap-6">
        <div className="bg-yellow-100 p-6 rounded-xl shadow">
          <p className="text-yellow-800 font-semibold">Citas pendientes</p>
          <h3 className="text-4xl font-bold mt-2">{stats.pending}</h3>
        </div>

        <div className="bg-green-100 p-6 rounded-xl shadow">
          <p className="text-green-800 font-semibold">Citas confirmadas</p>
          <h3 className="text-4xl font-bold mt-2">{stats.confirmed}</h3>
        </div>

        <div className="bg-red-100 p-6 rounded-xl shadow">
          <p className="text-red-800 font-semibold">Citas canceladas</p>
          <h3 className="text-4xl font-bold mt-2">{stats.cancelled}</h3>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-xl font-bold mb-4">Citas por estado</h2>

          <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#1d4ed8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-xl font-bold mb-4">Distribución de citas</h2>

          <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={90}
                  label
                >
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={["#facc15", "#16a34a", "#dc2626"][index]}
                    />
                  ))}
                </Pie>

                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-bold mb-4">Últimas citas registradas</h2>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border text-sm">
            <thead>
              <tr className="bg-blue-900 text-white">
                <th className="p-3 text-left font-semibold">ID</th>
                <th className="p-3 text-left font-semibold">Paciente</th>
                <th className="p-3 text-left font-semibold">Médico</th>
                <th className="p-3 text-left font-semibold">Fecha</th>
                <th className="p-3 text-left font-semibold">Estado</th>
                <th className="p-3 text-left font-semibold">Motivo</th>
              </tr>
            </thead>

            <tbody>
              {appointments.map((appointment, i) => (
                <tr key={appointment.id} className={`border-b transition hover:bg-blue-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                  <td className="p-3 text-gray-500">{appointment.id}</td>
                  <td className="p-3 font-medium">{appointment.paciente_id}</td>
                  <td className="p-3">{appointment.medico_id}</td>
                  <td className="p-3">{appointment.programada_en}</td>
                  <td className="p-3">{appointment.estado}</td>
                  <td className="p-3 max-w-xs truncate">{appointment.motivo}</td>
                </tr>
              ))}

              {appointments.length === 0 && (
                <tr>
                  <td colSpan="6" className="p-6 text-center text-gray-400 bg-white">
                    No hay citas registradas
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default DashboardPage;