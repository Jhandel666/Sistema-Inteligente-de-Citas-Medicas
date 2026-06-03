// Utilidades de normalización para La IA.
// Mantener aquí toda conversión de voz/texto a valores válidos del sistema.

const MONTHS_ES = {
  enero: "01",
  febrero: "02",
  marzo: "03",
  abril: "04",
  mayo: "05",
  junio: "06",
  julio: "07",
  agosto: "08",
  septiembre: "09",
  setiembre: "09",
  octubre: "10",
  noviembre: "11",
  diciembre: "12",
};

const WEEKDAYS_ES = {
  lunes: 1,
  martes: 2,
  miercoles: 3,
  miércoles: 3,
  jueves: 4,
  viernes: 5,
  sabado: 6,
  sábado: 6,
  domingo: 0,
};

function removeAccents(value = "") {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function normalizeEmail(raw = "") {
  let v = String(raw || "").toLowerCase().trim();

  // Limpiar prefijos: "correo:", "mi correo es", "email:", etc.
  v = v.replace(/^(?:mi\s+|el\s+|la\s+)?(?:correo|email|correo\s+electronico|correo\s+electrónico)\s*(?::\s*)?(?:\s+es\s+)?/i, "");

  v = v.replace(/\barroba\b/g, "@");
  v = v.replace(/\barrobe\b/g, "@");
  v = v.replace(/\barova\b/g, "@");
  v = v.replace(/\barroa\b/g, "@");
  v = v.replace(/\ba\s*rroba\b/g, "@");
  v = v.replace(/\ba\s*arroba\b/g, "@");
  v = v.replace(/\bat\b/g, "@");

  v = v.replace(/\bpunto\b/g, ".");
  v = v.replace(/\bdot\b/g, ".");

  v = v.replace(/\bguion\s+bajo\b/g, "_");
  v = v.replace(/\bguión\s+bajo\b/g, "_");
  v = v.replace(/\bguion\b/g, "-");
  v = v.replace(/\bguión\b/g, "-");

  v = v.replace(/\s*@\s*/g, "@");
  v = v.replace(/\s*\.\s*/g, ".");

  v = v.replace(/\.\s*com\b/g, ".com");
  v = v.replace(/\.\s*pe\b/g, ".pe");
  v = v.replace(/\.\s*es\b/g, ".es");
  v = v.replace(/\.\s*org\b/g, ".org");
  v = v.replace(/\.\s*net\b/g, ".net");
  v = v.replace(/\.\s*gob\b/g, ".gob");
  v = v.replace(/\.\s*edu\b/g, ".edu");

  v = removeAccents(v);
  v = v.replace(/ñ/g, "n");
  v = v.replace(/\s+/g, "");

  return v;
}

export function hasEmailLike(raw = "") {
  return /@|\barroba\b|\bat\b|\bpunto\s*(com|pe|org|net|edu|gob)\b/i.test(String(raw || ""));
}

export function extractEmailOnly(raw = "") {
  const normalized = normalizeEmail(raw);
  const match = normalized.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  return match ? match[0] : "";
}

export function isValidEmail(value = "") {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || ""));
}

export function normalizeDni(raw = "") {
  return String(raw || "").replace(/\D/g, "").slice(0, 8);
}

export function normalizePhone(raw = "") {
  return String(raw || "").replace(/\D/g, "").slice(0, 9);
}

export function normalizeGender(raw = "") {
  const t = removeAccents(String(raw || "").toLowerCase().trim());

  if (
    t.includes("masculino") ||
    t.includes("hombre") ||
    t.includes("varon") ||
    t.includes("mascu") ||
    t.includes("culino") ||
    t.includes("ulino")
  ) {
    return "masculino";
  }

  if (
    t.includes("femenino") ||
    t.includes("mujer") ||
    t.includes("fem") ||
    t.includes("menino")
  ) {
    return "femenino";
  }

  return t;
}

export function normalizePersonName(raw = "") {
  let original = String(raw || "");
  const lowerNoAccent = removeAccents(original.toLowerCase());

  // Soporte para correcciones de dictado:
  // "Yandel Jesús con J H" / "Yandel inicia con J H" -> "Jhandel Jesús".
  // No guarda literalmente "con J H" dentro del nombre.
  const hasJhHint = /(con|inicia con|empieza con|va con|es con)\s+j\s*h/.test(lowerNoAccent);

  let value = original
    .replace(/\b(?:doctor|doctora|dra|dr|médico|medico)\b\.?/gi, "")
    .replace(/\b(?:nombre|se llama|llamado|llamada|es)\b/gi, "")
    .replace(/\b(?:pero|inicia|empieza|va|con|es)\s+(?:con\s+)?j\s*h\b/gi, "")
    .replace(/\bj\s*h\b/gi, "")
    .replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  if (hasJhHint) {
    const parts = value.split(/\s+/).filter(Boolean);
    if (parts.length > 0) {
      const first = parts[0];
      // Caso común por voz: Yandel/Jandel dictado, pero el usuario aclara JH.
      if (/^[yj]andel$/i.test(removeAccents(first))) {
        parts[0] = "Jhandel";
      } else if (!/^jh/i.test(first) && first.length > 1) {
        parts[0] = "Jh" + first.slice(1);
      }
      value = parts.join(" ");
    }
  }

  return value;
}

function getNextWeekday(targetDay) {
  const now = new Date();
  const currentDay = now.getDay();
  let diff = targetDay - currentDay;
  if (diff <= 0) diff += 7;
  const result = new Date(now);
  result.setDate(now.getDate() + diff);
  return result;
}

export function normalizeSpanishDate(raw = "") {
  const v = String(raw || "").toLowerCase().trim();

  const correctionMatch = v.match(/(?:\bno\b|\bcorregir\b|\bcorreccion\b|\bes\b|\bfecha de nacimiento es\b)\s+(.+)$/i);
  if (correctionMatch && correctionMatch[1] && correctionMatch[1].trim() !== v) {
    const corrected = normalizeSpanishDate(correctionMatch[1].trim());
    if (/^\d{4}-\d{2}-\d{2}$/.test(corrected)) return corrected;
  }

  const numericNatural = v.match(/(?:el\s*)?(\d{1,2})\s*(?:de|del)?\s*(\d{1,2})\s*(?:de|del)?\s*(\d{4})/);
  if (numericNatural) {
    const [, d, m, y] = numericNatural;
    if (parseInt(d, 10) > 31 || parseInt(m, 10) > 12) return raw;
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  const isoMatch = v.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (isoMatch) {
    const [, y, m, d] = isoMatch;
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  const dmyMatch = v.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$/);
  if (dmyMatch) {
    let [, d, m, y] = dmyMatch;
    if (y.length === 2) y = "20" + y;
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  for (const [dayName, dayNum] of Object.entries(WEEKDAYS_ES)) {
    if (v.includes(dayName)) {
      const nextDate = getNextWeekday(dayNum);
      return `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, "0")}-${String(nextDate.getDate()).padStart(2, "0")}`;
    }
  }

  if (/\bhoy\b/.test(v)) {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  if (/\b(?:mañana|manana)\b/.test(v)) {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  const colonMatch = v.match(/^(\d{1,2})\s*[:]\s*(\d{1,2})\s*(?:d[ei]\s*l\s*)?(\d{4})$/);
  if (colonMatch) {
    let [, d, m, y] = colonMatch;
    if (parseInt(m, 10) > 12) [d, m] = [m, d];
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  let day = null;
  let month = null;
  let year = null;

  const y4 = v.match(/\b(\d{4})\b/);
  if (y4) year = parseInt(y4[1], 10);

  for (const [name, num] of Object.entries(MONTHS_ES)) {
    if (v.includes(name)) {
      month = num;
      break;
    }
  }

  const dayDigits = v.match(/(?:día|dia)\s+(\d{1,2})|(\b\d{1,2}\b)(?=\s*de\s+)/);
  if (dayDigits) day = parseInt(dayDigits[1] || dayDigits[2], 10);

  if (day && month && year) {
    return `${year}-${month}-${String(day).padStart(2, "0")}`;
  }

  return raw;
}

export function normalizeFieldValue(field, raw) {
  if (!field) return raw;

  const name = field.name;
  const type = field.type;

  if (type === "email" || ["correo", "correo_electronico", "email"].includes(name)) {
    return extractEmailOnly(raw);
  }

  if (["numero_documento", "document_number", "dni"].includes(name)) {
    return normalizeDni(raw);
  }

  if (["telefono", "phone"].includes(name)) {
    return normalizePhone(raw);
  }

  if (["genero", "sexo", "gender"].includes(name)) {
    return normalizeGender(raw);
  }

  if (["fecha_nacimiento", "birth_date"].includes(name) || type === "date" || type === "datetime-local") {
    return normalizeSpanishDate(raw);
  }

  if (["nombres", "apellidos", "first_name", "last_name"].includes(name)) {
    return normalizePersonName(raw);
  }

  return String(raw || "").trim();
}

export function fieldIsEmail(field) {
  return field?.type === "email" || ["correo", "correo_electronico", "email"].includes(field?.name);
}

export function fieldIsDni(field) {
  return ["numero_documento", "document_number", "dni"].includes(field?.name);
}

export function fieldIsPhone(field) {
  return ["telefono", "phone"].includes(field?.name);
}

export function fieldIsGender(field) {
  return ["genero", "sexo", "gender"].includes(field?.name);
}

export function fieldIsDate(field) {
  return ["fecha_nacimiento", "birth_date"].includes(field?.name) || field?.type === "date" || field?.type === "datetime-local";
}
