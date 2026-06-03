function MenuButton({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-3 rounded-lg transition ${
        active ? "bg-blue-700" : "hover:bg-blue-800"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

export default MenuButton;