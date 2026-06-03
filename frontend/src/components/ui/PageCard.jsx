function PageCard({ title, children, fullWidth = false }) {
  return (
    <section className={`mt-8 bg-white p-6 rounded-xl shadow ${fullWidth ? "w-full" : "max-w-3xl"}`}>
      <h3 className="text-xl font-bold mb-4">{title}</h3>
      {children}
    </section>
  );
}

export default PageCard;