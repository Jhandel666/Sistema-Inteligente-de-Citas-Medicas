// Motor de corrección de campos de La IA.
// Evita que frases como "va con JH" se guarden como apellido/correo.

const FIELD_ALIASES = {
  nombres: ["nombre", "nombres", "primer nombre", "nombre del paciente", "nombre del médico", "nombre del medico"],
  first_name: ["nombre", "nombres", "primer nombre"],
  apellidos: ["apellido", "apellidos", "apellido paterno", "apellido materno"],
  last_name: ["apellido", "apellidos"],
  numero_documento: ["dni", "documento", "número de documento", "numero de documento"],
  document_number: ["dni", "documento", "número de documento", "numero de documento"],
  telefono: ["telefono", "teléfono", "celular", "número de celular", "numero de celular"],
  phone: ["telefono", "teléfono", "celular"],
  correo: ["correo", "correo electrónico", "correo electronico", "email"],
  correo_electronico: ["correo", "correo electrónico", "correo electronico", "email"],
  email: ["correo", "correo electrónico", "correo electronico", "email"],
  fecha_nacimiento: ["fecha", "fecha de nacimiento", "nacimiento", "cumpleaños"],
  birth_date: ["fecha", "fecha de nacimiento", "nacimiento"],
  genero: ["genero", "género", "sexo"],
  sexo: ["genero", "género", "sexo"],
  gender: ["genero", "género", "sexo"],
  especialidad: ["especialidad"],
  specialty: ["especialidad"],
  motivo: ["motivo", "motivo de cita", "motivo de la cita"],
  reason: ["motivo", "motivo de cita", "motivo de la cita"],
};

export function isCorrectionIntent(raw = "") {
  const t = String(raw || "").toLowerCase();

  return [
    "corrige",
    "corregir",
    "corrección",
    "correccion",
    "corrijamos",
    "no es",
    "quise decir",
    "escuchaste mal",
    "está mal",
    "esta mal",
    "está incorrecto",
    "esta incorrecto",
    "es con",
    "va con",
    "empieza con",
    "inicia con",
    "se escribe",
    "la primera letra",
    "la inicial",
    "debe decir",
    "cambiar",
    "rectificar",
    "modificar",
  ].some((x) => t.includes(x));
}

export function getFieldNameFromText(text = "", fields = []) {
  const t = String(text || "").toLowerCase();

  for (const field of fields || []) {
    const aliases = FIELD_ALIASES[field.name] || [field.name, field.label].filter(Boolean);
    if (aliases.some((alias) => alias && t.includes(alias.toLowerCase()))) {
      return field.name;
    }
  }

  for (const [fieldName, aliases] of Object.entries(FIELD_ALIASES)) {
    if (aliases.some((alias) => t.includes(alias.toLowerCase()))) {
      const exists = fields?.find((f) => f.name === fieldName);
      if (exists) return exists.name;
    }
  }

  return null;
}

export function correctionTargetField(session, text = "") {
  if (!session || !session.fields?.length) return null;

  const explicitName = getFieldNameFromText(text, session.fields);
  if (explicitName) {
    return session.fields.find((f) => f.name === explicitName) || null;
  }

  const previousIdx = Math.max(0, session.currentFieldIndex - 1);
  return session.fields[previousIdx] || null;
}

export function buildCorrectionQuestion(field) {
  if (!field) return "¿Qué campo deseas corregir?";

  const label = String(field.label || field.name || "campo").toLowerCase();

  return `Entiendo, vamos a corregir ${label}. Dímelo nuevamente completo.`;
}

export function buildFinalSummary(entity, values = {}) {
  const title = {
    patient: "paciente",
    doctor: "médico",
    appointment: "cita médica",
    paciente: "paciente",
    medico: "médico",
    cita: "cita médica",
  }[entity] || entity || "registro";

  const labels = {
    nombres: "Nombres",
    apellidos: "Apellidos",
    numero_documento: "DNI",
    correo: "Correo",
    correo_electronico: "Correo",
    telefono: "Teléfono",
    fecha_nacimiento: "Fecha de nacimiento",
    genero: "Género",
    sexo: "Sexo",
    especialidad: "Especialidad",
    motivo: "Motivo",
    fecha_hora_cita: "Fecha y hora",
    first_name: "Nombres",
    last_name: "Apellidos",
    document_number: "DNI",
    email: "Correo",
    phone: "Teléfono",
    birth_date: "Fecha de nacimiento",
    gender: "Género",
    specialty: "Especialidad",
    reason: "Motivo",
    scheduled_at: "Fecha y hora",
  };

  const lines = Object.entries(values || {})
    .filter(([, value]) => value !== undefined && value !== null && String(value).trim() !== "")
    .map(([key, value]) => `• ${labels[key] || key}: ${value}`)
    .join("\n");

  return `Resumen del ${title}:\n\n${lines || "Sin datos."}\n\n¿Confirmas guardar? Responde: sí, no o corregir campo.`;
}
