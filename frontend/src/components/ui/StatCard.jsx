function StatCard({ title, value }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow">
      <p className="text-gray-500">{title}</p>
      <h3 className="text-3xl font-bold text-blue-800">{value}</h3>
    </div>
  );
}

export default StatCard;