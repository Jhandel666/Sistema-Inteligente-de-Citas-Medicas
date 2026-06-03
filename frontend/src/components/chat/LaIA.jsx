import { useState, useRef, useEffect, useCallback } from "react";
import { Keyboard, X, Volume2, VolumeX, Bug, Maximize2, Minimize2, Power, PowerOff } from "lucide-react";
import api from "../../services/api";
import { useFormFilling } from "../../context/FormFillingContext";
import { generateTicketPdf } from "../../modules/tickets/ticketPdfService";
import "../../laia-jarvis.css";

// ─── Normalizadores de entrada de voz ───────────────────────────────────────

function normalizeEmail(raw) {
  let v = raw.toLowerCase().trim();

  // Limpiar prefijos: "correo:", "mi correo es", "email:", etc.
  v = v.replace(/^(?:mi\s+|el\s+|la\s+)?(?:correo|email|correo\s+electronico|correo\s+electrónico)\s*(?::\s*)?(?:\s+es\s+)?/i, "");

  // "arroba" y variantes comunes por voz → @
  v = v.replace(/\barroba\b/g, "@");
  v = v.replace(/\broba\b/g, "@");
  v = v.replace(/\barrobe\b/g, "@");
  v = v.replace(/\barroba\b/g, "@");
  v = v.replace(/\barova\b/g, "@");
  v = v.replace(/\barroa\b/g, "@");
  v = v.replace(/\ba\s*rroba\b/g, "@");
  v = v.replace(/\ba\s*arroba\b/g, "@");

  // "en" como reemplazo de @ (ej: "jhandel en gmail")
  v = v.replace(/\b\s*en\s*(?=[a-z]+\s*(?:punto|dot|\.|com|es|pe))\b/g, "@");

  // "at" como @
  v = v.replace(/\bat\b/g, "@");

  // "punto" → .
  v = v.replace(/\bpunto\b/g, ".");
  v = v.replace(/\bpunto\b/g, ".");

  // "dot" → .
  v = v.replace(/\bdot\b/g, ".");

  // "guion bajo" → _
  v = v.replace(/\bguion\s+bajo\b/g, "_");
  v = v.replace(/\bguión\s+bajo\b/g, "_");

  // "guion" → -
  v = v.replace(/\bguion\b/g, "-");
  v = v.replace(/\bguión\b/g, "-");

  // Limpiar espacios alrededor de @ y .
  v = v.replace(/\s*@\s*/g, "@");
  v = v.replace(/\s*\.\s*/g, ".");

  // "punto com" → ".com", "punto pe" → ".pe", etc.
  v = v.replace(/\.\s*com\b/g, ".com");
  v = v.replace(/\.\s*pe\b/g, ".pe");
  v = v.replace(/\.\s*es\b/g, ".es");
  v = v.replace(/\.\s*org\b/g, ".org");
  v = v.replace(/\.\s*net\b/g, ".net");
  v = v.replace(/\.\s*gob\b/g, ".gob");
  v = v.replace(/\.\s*edu\b/g, ".edu");

  // Eliminar espacios restantes
  v = v.replace(/\s+/g, "");

  // Eliminar acentos (Chávez → Chavez)
  v = v.replace(/[áäà]/g, "a").replace(/[éëè]/g, "e").replace(/[íïì]/g, "i")
       .replace(/[óöò]/g, "o").replace(/[úüù]/g, "u").replace(/ñ/g, "n");

  // Extraer solo email del texto
  const emailMatch = v.match(/[a-zA-Z0-9._%+\-À-ÿ]+@[a-zA-Z0-9.\-À-ÿ]+\.[a-zA-ZÀ-ÿ]{2,}/);
  if (emailMatch) return emailMatch[0];

  return v;
}

const WEEKDAYS_ES = {
  lunes: 1, martes: 2, miercoles: 3, miércoles: 3,
  jueves: 4, viernes: 5, sabado: 6, sábado: 6, domingo: 0,
};

const MONTHS_ES = {
  enero: "01", febrero: "02", marzo: "03", abril: "04",
  mayo: "05", junio: "06", julio: "07", agosto: "08",
  septiembre: "09", octubre: "10", noviembre: "11", diciembre: "12",
  setiembre: "09",
};

function parseSpanishNumber(word) {
  const map = {
    cero: 0, uno: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5,
    seis: 6, siete: 7, ocho: 8, nueve: 9, diez: 10,
    once: 11, doce: 12, trece: 13, catorce: 14, quince: 15,
    dieciseis: 16, diecisiete: 17, dieciocho: 18, diecinueve: 19,
    veinte: 20, veintiuno: 21, veintidos: 22, veintitres: 23,
    veinticuatro: 24, veinticinco: 25, veintiseis: 26, veintisiete: 27,
    veintiocho: 28, veintinueve: 29,
    treinta: 30, cuarenta: 40, cincuenta: 50,
    sesenta: 60, setenta: 70, ochenta: 80, noventa: 90,
    cien: 100, ciento: 100, quinientos: 500, seiscientos: 600,
    setecientos: 700, ochocientos: 800, novecientos: 900, mil: 1000,
  };
  return map[word] ?? null;
}

function extractEmailOnly(raw) {
  const normalized = normalizeEmail(String(raw || ""));
  const match = normalized.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  return match ? match[0] : "";
}

function parseSpanishYear(text) {
  const words = text.toLowerCase().split(/\s+/);
  let total = 0;
  let current = 0;
  for (const w of words) {
    const n = parseSpanishNumber(w);
    if (n === null) {
      const compound = w.match(/^(veinti|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa)(\d{1})$/);
      if (compound) {
        current += parseInt(compound[1]) + parseInt(compound[2]);
      }
      continue;
    }
    if (n >= 1000) {
      current = Math.max(current, 1) * n;
      total += current;
      current = 0;
    } else if (n >= 100) {
      current = Math.max(current, 1) * n;
    } else if (n >= 30) {
      current += n;
    } else if (n === 20) {
      current += n;
    } else {
      current += n;
    }
  }
  total += current;
  return total > 0 ? total : null;
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

function parseSpanishDate(raw) {
  const v = raw.toLowerCase().trim();

  // Correcciones por voz: tomar solo la fecha después de "no", "corregir", "es", etc.
  // Ej: "2022 03 del 2000 no el 3 del 7 de 2022" => "el 3 del 7 de 2022"
  const correctionMatch = v.match(/(?:\bno\b|\bcorregir\b|\bcorreccion\b|\bes\b|\bfecha de nacimiento es\b)\s+(.+)$/i);
  if (correctionMatch && correctionMatch[1] && correctionMatch[1].trim() !== v) {
    const corrected = parseSpanishDate(correctionMatch[1].trim());
    if (/^\d{4}-\d{2}-\d{2}$/.test(corrected)) return corrected;
  }

  // DD de MM de YYYY / "el 03 del 08 2022" / "3 del 7 de 2022"
  const numericNatural = v.match(/(?:el\s*)?(\d{1,2})\s*(?:de|del)?\s*(\d{1,2})\s*(?:de|del)?\s*(\d{4})/);
  if (numericNatural) {
    let [, d, m, y] = numericNatural;
    if (parseInt(d) > 31 || parseInt(m) > 12) return raw;
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  // ISO directo
  const isoMatch = v.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (isoMatch) {
    const [, y, m, d] = isoMatch;
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  // DD/MM/YYYY o DD-MM-YYYY
  const dmyMatch = v.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$/);
  if (dmyMatch) {
    let [, d, m, y] = dmyMatch;
    if (y.length === 2) y = "20" + y;
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  // Días de la semana relativos
  for (const [dayName, dayNum] of Object.entries(WEEKDAYS_ES)) {
    if (v.includes(dayName)) {
      const nextDate = getNextWeekday(dayNum);
      return `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, "0")}-${String(nextDate.getDate()).padStart(2, "0")}`;
    }
  }

  // Fechas relativas en español
  if (/\bhoy\b/.test(v)) {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  if (/\b(?:mañana|manana)\b/.test(v)) {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  if (/\b(?:pasado\s*mañana|pasado\s*manana|pasado\s*ma~ana)\b/.test(v)) {
    const d = new Date();
    d.setDate(d.getDate() + 2);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  if (/\b(?:pr[oó]xima\s*semana|semana\s*que\s*viene)\b/.test(v)) {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  // DD:MM del YYYY o DD:MM:YYYY (voz dice "6:11 del 2006" para 6 de noviembre)
  const colonMatch = v.match(/^(\d{1,2})\s*[:]\s*(\d{1,2})\s*(?:d[ei]\s*l\s*)?(\d{4})$/);
  if (colonMatch) {
    let [, d, m, y] = colonMatch;
    if (parseInt(m) > 12) { [d, m] = [m, d]; }
    return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
  }

  // Español natural: "15 de mayo de 1990", "quince de mayo de mil novecientos noventa"
  let day = null, month = null, year = null;

  const y4 = v.match(/\b(\d{4})\b/);
  const y2 = v.match(/\b(\d{2})\b\s*$/);
  if (y4) {
    year = parseInt(y4[1]);
  } else if (y2) {
    year = parseInt(y2[1]);
    if (year >= 0 && year <= 49) year += 2000;
    else if (year >= 50 && year <= 99) year += 1900;
  } else {
    const yWords = v.match(/((?:\w+\s+){0,2}mil\s+(?:\w+\s+)*\w+)/);
    if (yWords) year = parseSpanishYear(yWords[1]);
  }

  for (const [name, num] of Object.entries(MONTHS_ES)) {
    if (v.includes(name)) {
      month = num;
      break;
    }
  }

  const dayDigits = v.match(/(?:día|dia)\s+(\d{1,2})|(\b\d{1,2}\b)(?=\s*de\s+)/);
  if (dayDigits) {
    day = parseInt(dayDigits[1] || dayDigits[2]);
  } else {
    const dayWords = v.match(/\b(uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciseis|diecisiete|dieciocho|diecinueve|veinte|veintiuno|veintidos|veintitres|veinticuatro|veinticinco|veintiseis|veintisiete|veintiocho|veintinueve|treinta|treinta\s+y\s+uno)\b/);
    if (dayWords) {
      day = parseSpanishNumber(dayWords[1]) || parseInt(dayWords[1]);
    }
  }

  if (day && month && year) {
    const d = new Date(year, parseInt(month) - 1, day);
    if (!isNaN(d.getTime())) {
      return `${year}-${month}-${String(day).padStart(2, "0")}`;
    }
  }

  // Fallback: Date.parse
  const ts = Date.parse(v);
  if (!isNaN(ts)) {
    const d = new Date(ts);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  return raw;
}


function hasEmailLike(raw) {
  return /@|\barroba\b|\bat\b/i.test(String(raw || ""));
}

function isValidEmailValue(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || ""));
}

function normalizePersonName(raw) {
  return String(raw || "")
    .replace(/\b(?:doctor|doctora|dra|dr|médico|medico)\b\.?/gi, "")
    .replace(/\b(?:nombre|se llama|llamado|llamada|es)\b/gi, "")
    .replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function splitFullName(raw) {
  const clean = normalizePersonName(raw);
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length < 2) return null;
  return {
    first_name: parts[0],
    last_name: parts.slice(1).join(" "),
  };
}

function isCommandOnlyDoctor(raw) {
  const t = String(raw || "").toLowerCase();
  return /(crear|registrar|agregar|nuevo|nueva)/.test(t) && /(médico|medico|doctor|doctora)/.test(t) && !hasEmailLike(t);
}

function toGenderSelect(v) {
  if (!v) return "";
  const low = String(v).toLowerCase();
  if (low === "masculino" || low === "m") return "M";
  if (low === "femenino" || low === "f") return "F";
  return v;
}

function normalizeFieldValue(field, raw) {
  if (!raw || typeof raw !== "string") return raw;
  const trimmed = raw.trim();
  if (field.type === "email") return normalizeEmail(trimmed);
  if (field.name === "birth_date" || field.type === "date") return parseSpanishDate(trimmed);
  if (field.type === "datetime-local") return parseSpanishDate(trimmed);
  if (field.name === "document_number" || field.name === "dni") return trimmed.replace(/\D/g, "");
  if (field.name === "phone" || field.name === "telefono") return trimmed.replace(/\s+/g, "");
  return trimmed;
}

// ─── Fin normalizadores ─────────────────────────────────────────────────────

const LA_IA_AVATAR = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='48' fill='%231e3a5f'/%3E%3Ctext x='50' y='62' font-size='32' text-anchor='middle' fill='white' font-family='Arial'%3ELA%3C/text%3E%3C/svg%3E";

const WAKE = ["ey eva", "hey eva", "eva salud", "asistente eva", "la ia", "asistente la ia", "ey la ia", "hey la ia"];
function isWake(t) { return WAKE.some(w => t.toLowerCase().includes(w)); }

const DESACTIVAR = ["desactivate", "desactivar", "desactivada", "desactívate", "desactivarme", "apágate", "apagate", "cállate", "callate", "silencio", "duermete", "duérmete"];
function isDesactivar(t) { return DESACTIVAR.some(w => t.toLowerCase().includes(w)); }

const CREATE_ACTIONS = new Set(["crear_paciente", "crear_medico", "agendar_cita"]);
const SIMPLE_CREATE = new Set(["crear_paciente", "crear_medico"]);

function isCorrectionIntent(raw) {
  const t = String(raw || "").toLowerCase();

  return [
    "corrige",
    "corregir",
    "corrección",
    "no es",
    "quise decir",
    "escuchaste mal",
    "está mal",
    "esta mal",
    "es con",
    "va con",
    "empieza con",
    "inicia con",
    "se escribe",
    "la primera letra",
    "la inicial",
    "debe decir",
    "cambiar"
  ].some(x => t.includes(x));
}

function correctionTargetField(session) {
  if (!session || !session.fields?.length) return null;
  const previousIdx = Math.max(0, session.currentFieldIndex - 1);
  return session.fields[previousIdx] || null;
}

function LaIA({ setActivePage, onAction }) {
  const { session, startFilling, setCurrentValue, nextField, resetField, setFieldIndex, completeFilling, cancelFilling, resumeFilling, getSession, setRiskData } = useFormFilling();

  const [view, setView] = useState("badge");
  const [state, setState] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [showDebug, setShowDebug] = useState(false);
  const [debugLog, setDebugLog] = useState([]);
  const [browserError, setBrowserError] = useState("");
  const [disabled, setDisabled] = useState(false);

  const ar = useRef(true);
  const fullRef = useRef(false);
  const wokeRef = useRef(false);
  const wr = useRef(null);
  const cr = useRef(null);
  const wakeCount = useRef(0);
  const warnShown = useRef(false);
  const wakeFn = useRef(null);
  const cmdFn = useRef(null);
  const disabledRef = useRef(false);
  const chainRef = useRef(null);
  const processInputRef = useRef(null);

  const correctionHistory = useRef([]);
const awaitingFinalConfirmation = useRef(false);

  const log = useCallback((m) => {
    console.log(`[LaIA] ${m}`);
    setDebugLog(p => [...p.slice(-19), `${new Date().toLocaleTimeString()}: ${m}`]);
  }, []);

  const voiceRef = useRef(null);

  const speak = useCallback((text, onDone) => {
    if (!ttsEnabled || disabledRef.current) { setTimeout(() => onDone?.(), 100); return; }
    const clean = text.replace(/\*+/g, "").replace(/\n/g, ". ").replace(/\s+/g, " ").trim();
    window.speechSynthesis?.cancel();
    const u = new SpeechSynthesisUtterance(clean);
    u.lang = "es-PE"; u.rate = 1.1; u.pitch = 1.0;
    if (voiceRef.current) u.voice = voiceRef.current;
    u.onstart = () => { log("tts"); setState("speaking"); };
    u.onend = () => { log("tts end"); setState("idle"); setTimeout(() => onDone?.(), 300); };
    u.onerror = () => { setState("idle"); };
    window.speechSynthesis.speak(u);
  }, [ttsEnabled, log]);

  const setVoiceGender = useCallback((gender) => {
    const select = () => {
      const voices = window.speechSynthesis.getVoices();
      if (!voices.length) {
        window.speechSynthesis.addEventListener("voiceschanged", select, { once: true });
        return;
      }
      if (gender === "female") {
        voiceRef.current = voices.find(v => /helena|sabina|zira|google español/i.test(v.name))
          || voices.find(v => /female|mujer/i.test(v.name))
          || voices.find(v => v.lang.startsWith("es"));
        log(`voz femenina: ${voiceRef.current?.name || "ninguna disponible"}`);
      } else {
        voiceRef.current = null;
      }
    };
    select();
  }, [log]);

  // ─── Alternar desactivación ─────────────────────────────────────
  const toggleDisabled = useCallback((val) => {
    disabledRef.current = val;
    setDisabled(val);
    if (val) {
      window.speechSynthesis?.cancel();
      setView("badge");
      setState("idle");
      log("desactivada");
    } else {
      log("reactivada");
      fullRef.current = false;
      setTimeout(() => { if (ar.current) wakeFn.current?.(); }, 500);
    }
  }, [log]);

  function buildFinalSummary(entity, values) {
  const title = {
    patient: "paciente",
    doctor: "médico",
    appointment: "cita médica",
  }[entity] || entity;

  const lines = Object.entries(values || {})
    .map(([key, value]) => `• ${key}: ${value}`)
    .join("\n");

  return `Resumen del ${title}:\n\n${lines}\n\n¿Confirmas guardar? Responde: sí, no o corregir campo.`;
}

  // ─── Llenar campo actual ───────────────────────────────────────
  const handleFieldValue = useCallback(async (rawValue) => {
    if (!session || session.completed || session.cancelled) return false;
    const fields = session.fields;
    const idx = session.currentFieldIndex;
    if (idx >= fields.length) return false;

    const field = fields[idx];
    const value = normalizeFieldValue(field, rawValue);

    // ── Reglas críticas para médicos ──
    // No permitir que un correo termine guardado como nombre del médico.
    if (session.entity === "doctor" && (field.name === "first_name" || field.name === "last_name") && hasEmailLike(rawValue)) {
      const question = field.name === "first_name"
        ? "Ese dato parece un correo. Ahora necesito solo los nombres del médico."
        : "Ese dato parece un correo. Ahora necesito solo los apellidos del médico.";
      log(`dato rechazado para ${field.name}: parece correo "${String(rawValue).slice(0, 40)}"`);
      setResponse(question);
      setTranscript("");
      setState("idle");
      speak(question, () => cmdFn.current?.());
      return true;
    }

    // Médico: respetar el schema real del backend:
    // first_name = nombres, last_name = apellidos, specialty = especialidad, email = correo.
    // No dividir nombres automáticamente ni saltar apellidos.
    if (session.entity === "doctor" && field.name === "first_name") {
      if (isCommandOnlyDoctor(rawValue)) {
        const question = "¿Cuáles son los nombres del médico? Ejemplo: Luis Alberto.";
        setResponse(question);
        setTranscript("");
        setState("idle");
        speak(question, () => cmdFn.current?.());
        return true;
      }

      const nombres = normalizePersonName(rawValue);

      if (!nombres || nombres.length < 2) {
        const question = "Nombre inválido. Dime los nombres del médico. Ejemplo: Luis Alberto.";
        setResponse(question);
        setTranscript("");
        setState("idle");
        speak(question, () => cmdFn.current?.());
        return true;
      }

      log(`rellenando first_name: "${nombres}"`);
      setCurrentValue("first_name", nombres);

      const lastIdx = fields.findIndex(f => f.name === "last_name");
      if (lastIdx >= 0) {
        setFieldIndex(lastIdx);
        const question = "¿Cuáles son los apellidos del médico? Ejemplo: Quispe Mamani.";
        setResponse(question);
        setTranscript("");
        speak(question, () => cmdFn.current?.());
        return true;
      }
    }

    if (session.entity === "doctor" && field.name === "last_name") {
      if (hasEmailLike(rawValue)) {
        const question = "Eso parece un correo. Ahora necesito solo los apellidos del médico.";
        setResponse(question);
        setTranscript("");
        setState("idle");
        speak(question, () => cmdFn.current?.());
        return true;
      }

      const apellidos = normalizePersonName(rawValue);

      if (!apellidos || apellidos.length < 2) {
        const question = "Apellido inválido. Dime los apellidos del médico. Ejemplo: Quispe Mamani.";
        setResponse(question);
        setTranscript("");
        setState("idle");
        speak(question, () => cmdFn.current?.());
        return true;
      }

      log(`rellenando last_name: "${apellidos}"`);
      setCurrentValue("last_name", apellidos);

      const specIdx = fields.findIndex(f => f.name === "specialty");

      if (specIdx >= 0) {
        setFieldIndex(specIdx);
        const question = `¿Cuál es la especialidad del médico? Ejemplo: Cardiología.`;
        setResponse(question);
        setTranscript("");
        speak(question, () => cmdFn.current?.());
        return true;
      }
    }

    if (field.name === "email" || field.type === "email") {
  const emailOnly = extractEmailOnly(rawValue);

  if (!emailOnly || !isValidEmailValue(emailOnly)) {
    const question =
      "Correo inválido. Dime el correo completo. Ejemplo: jhandeljesuschavezmiranda4 arroba gmail punto com.";

    log(`email inválido: "${rawValue}"`);
    setResponse(question);
    setTranscript("");
    setState("idle");
    speak(question, () => cmdFn.current?.());
    return true;
  }

  log(`rellenando ${field.name}: "${emailOnly}"`);
  setCurrentValue(field.name, emailOnly);

  const nextIdx = idx + 1;

  if (nextIdx >= fields.length) {
  completeFilling();
  awaitingFinalConfirmation.current = true;

  const currentSession = getSession();
  const msg = buildFinalSummary(currentSession?.entity, currentSession?.values);

  setResponse(msg);
  setTranscript("");
  speak(msg, () => cmdFn.current?.());
  } else {
    const nextField = fields[nextIdx];
    const question = `¿Cuál es ${nextField.label.toLowerCase()}?`;
    setResponse(question);
    setTranscript("");
    speak(question, () => cmdFn.current?.());
  }

  return true;
}

if ((field.type === "date" || field.type === "datetime-local" || field.name === "birth_date") && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?$/.test(value)) {
  const question = `No entendí bien la fecha. Dímela así: día, mes y año. Ejemplo: 03 de junio de 2022.`;
  log(`fecha invalida para ${field.name}: "${value}"`);
  setResponse(question);
  setTranscript("");
  setState("idle");
  speak(question, () => cmdFn.current?.());
  return true;
}

if ((field.name === "scheduled_at" || field.type === "datetime-local") && new Date(value) < new Date()) {
  const question = "La fecha de la cita no puede ser en el pasado. Dime una fecha y hora futura.";
  log(`fecha pasada para ${field.name}: "${value}"`);
  setResponse(question);
  setTranscript("");
  setState("idle");
  speak(question, () => cmdFn.current?.());
  return true;
}

if ((field.name === "document_number" || field.name === "dni") && value.replace(/\D/g, "").length !== 8) {
  const question = `El DNI debe tener exactamente 8 dígitos. Repítelo número por número, por ejemplo: 1 2 3 4 5 6 7 8.`;
  log(`dni invalido: "${value}"`);
  setResponse(question);
  setTranscript("");
  setState("idle");
  speak(question, () => cmdFn.current?.());
  return true;
}

if (field.name === "phone" || field.name === "telefono") {
  const digits = value.replace(/\D/g, "");
  if (digits.length !== 9 || !digits.startsWith("9")) {
    const question = `El teléfono debe tener 9 dígitos y empezar con 9. Ejemplo: 9 1 8 5 1 2 3 0 1.`;
    log(`telefono invalido: "${value}"`);
    setResponse(question);
    setTranscript("");
    setState("idle");
    speak(question, () => cmdFn.current?.());
    return true;
  }
}

log(`rellenando ${field.name}: "${String(value).slice(0, 40)}" (raw: "${String(rawValue).slice(0, 30)}")`);
setCurrentValue(field.name, value);

const nextIdx = idx + 1;
if (nextIdx >= fields.length) {
  completeFilling();
  const msg = "Todos los datos están completos. Guardando...";
  setResponse(msg);
  setTranscript("");
  speak(msg, () => {
    submitForm();
  });
} else {
  const nextField = fields[nextIdx];
  const question = `¿Cuál es ${nextField.label.toLowerCase()}?`;
  setResponse(question);
  setTranscript("");
  speak(question, () => cmdFn.current?.());
}
return true;
}, [session, setCurrentValue, completeFilling, speak]);
  // ─── Enviar formulario completo ─────────────────────────────────
  const submitForm = useCallback(async () => {
    const s = getSession();
    if (!s) return;
    const vals = s.values;
    const entity = s.entity;
    log(`enviando ${entity}: ${JSON.stringify(vals).slice(0, 100)}`);
    setState("processing");
    try {
      const res = await api.post("/assistant/form-submit", { entity, data: vals });
      const data = res.data;
      if (data.type === "error") {
        const voice = data.voice || "Error al guardar.";
        setResponse(data.message || "Error al guardar.");
        cancelFilling();
        speak(voice, () => cmdFn.current?.());
        return;
      }
      const msg = data.message || "Registrado correctamente.";
      setResponse(msg);
      if (data.target && setActivePage) setActivePage(data.target);
      if (onAction && data.target) onAction();
      cancelFilling();

      const chain = chainRef.current;
      if (chain && (entity === "patient" || entity === "doctor") && chain.action === "agendar_cita") {
        chainRef.current = null;
        setTimeout(() => processInputRef.current?.(chain.text), 600);
        return;
      }
      chainRef.current = null;

      if (data.voice) speak(data.voice, () => cmdFn.current?.());
      else speak(msg, () => cmdFn.current?.());
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 422 && Array.isArray(detail)) {
        const getLoc = (d) => { const loc = d.loc || []; return loc[loc.length - 1]; };
        const badField = detail.map(getLoc).filter(Boolean)[0];
        log(`error validación en: ${badField || "desconocido"}`);

        const field = badField && s.fields ? s.fields.find(f => f.name === badField) : null;
        const errMsg = detail.find(d => getLoc(d) === badField)?.msg || "dato inválido";
        if (field && badField) {
          resetField(badField);
          const badIdx = s.fields.findIndex(f => f.name === badField);
          if (badIdx >= 0) setFieldIndex(badIdx);
        }

        const label = field ? field.label.toLowerCase() : badField || "campo";
        const question = `El **${label}** es incorrecto: ${errMsg}. Dímelo de nuevo para corregir solo ese campo.`;
        setResponse(question);
        setState("idle");
        speak(question, () => cmdFn.current?.());
      } else {
        const msg = err.response?.data?.detail || err.response?.data?.message || "Error de conexión.";
        setResponse(`Error: ${typeof msg === "string" ? msg : JSON.stringify(msg)}`);
        cancelFilling();
        speak("Error al guardar. Intenta de nuevo.", () => cmdFn.current?.());
      }
    }
  }, [getSession, cancelFilling, resetField, setFieldIndex, startFilling, speak, setActivePage, onAction, log]);

  // ─── Iniciar sesión de llenado ──────────────────────────────────
  const startCreateFlow = useCallback(async (action, prefillData = {}) => {
    const entityMap = { crear_paciente: "patient", crear_medico: "doctor", agendar_cita: "appointment" };
    const entity = entityMap[action];
    if (!entity) return false;
    log(`iniciando flujo crear ${entity} con ${Object.keys(prefillData).length} campos prellenados`);
    try {
      const res = await api.get(`/assistant/form-schema/${entity}`);
      const schema = res.data;
      if (schema.error) { log(`schema error: ${schema.error}`); return false; }
      const fields = schema.fields;
      let safePrefill = { ...(prefillData || {}) };

      // Protección: para crear médico, nunca aceptar correos o frases de comando como nombre.
      if (entity === "doctor") {
        if (safePrefill.first_name && hasEmailLike(safePrefill.first_name)) delete safePrefill.first_name;
        if (safePrefill.last_name && hasEmailLike(safePrefill.last_name)) delete safePrefill.last_name;
        if (safePrefill.first_name && isCommandOnlyDoctor(safePrefill.first_name)) delete safePrefill.first_name;
        if (safePrefill.email && !isValidEmailValue(normalizeEmail(safePrefill.email))) delete safePrefill.email;
      }

      startFilling(entity, fields, safePrefill);

      const targetMap = { patient: "patients", doctor: "doctors", appointment: "appointments" };
      const tgt = targetMap[entity];
      if (tgt && setActivePage) setActivePage(tgt);
      if (onAction) onAction();

      const firstUnfilled = fields.find(f => !safePrefill[f.name]);
      if (firstUnfilled) {
        let question = `Voy a guiarte paso a paso. ¿Cuál es ${firstUnfilled.label.toLowerCase()}?`;
        if (entity === "doctor" && firstUnfilled.name === "first_name") {
          question = "Voy a guiarte paso a paso. ¿Cuáles son los nombres del médico? Ejemplo: Luis Alberto.";
        }
        if (entity === "doctor" && firstUnfilled.name === "email") {
          question = "¿Cuál es el correo electrónico real del médico? Ejemplo: luis.quispe@gmail.com.";
        }
        setResponse(question);
        setTranscript("");
        speak(question, () => cmdFn.current?.());
      } else {
        completeFilling();
        const msg = "Todos los datos están completos. Guardando...";
        setResponse(msg);
        setTranscript("");
        speak(msg, () => { submitForm(); });
      }
      return true;
    } catch (e) {
      log(`error al obtener schema: ${e.message}`);
      return false;
    }
  }, [startFilling, completeFilling, submitForm, speak, setActivePage, onAction, log]);

  // ─── Procesar texto (voz o escrito) ─────────────────────────────
  const processInput = useCallback(async (text) => {
    if (!text) return;
    log(`input: "${text.slice(0, 60)}"`);

    if (disabledRef.current) {
      if (isWake(text)) {
        toggleDisabled(false);
        await new Promise(r => setTimeout(r, 800));
        const msg = "Hola Admin, ¿en qué puedo ayudarte?";
        setResponse(msg);
        setTranscript("");
        speak(msg, () => cmdFn.current?.());
      }
      return;
    }

    if (isDesactivar(text)) {
      toggleDisabled(true);
      setResponse("La IA desactivada. Di 'Eva Salud' o 'La IA' para reactivarme.");
      return;
    }

    if (/\b(continuar|retomar|seguir)\b.*\b(registro|formulario|cita|paciente|médico|medico)?\b/i.test(text)) {
      const resumed = resumeFilling?.();
      if (resumed && resumed.fields && resumed.currentFieldIndex < resumed.fields.length) {
        const f = resumed.fields[resumed.currentFieldIndex];
        const question = `Retomamos donde quedó. ¿Cuál es ${f.label.toLowerCase()}?`;
        setResponse(question);
        setTranscript("");
        setState("idle");
        speak(question, () => cmdFn.current?.());
        return;
      }
    }

    // ── Cambio de voz directo (sin backend) ──
    const vozClean = text.toLowerCase().trim();
    const esCambioVoz = /cambi(?:a|e|ar)\s+.*(?:voz|tono)/.test(vozClean) || /(?:voz|tono)\s+(?:de\s+)?(?:mujer|femenina|hombre|varon|masculina)/.test(vozClean);
    if (esCambioVoz) {
      const esMujer = /mujer|femenina/.test(vozClean);
      const esHombre = /hombre|varon|masculino/.test(vozClean);
      let msg;
      if (esMujer) {
        setVoiceGender("female");
        msg = "¡Claro! Cambiando la voz a femenina.";
      } else if (esHombre) {
        setVoiceGender("male");
        msg = "¡Claro! Cambiando la voz a masculina.";
      } else {
        if (voiceRef.current !== null) {
          setVoiceGender("male");
          msg = "¡Claro! Cambiando la voz a masculina.";
        } else {
          setVoiceGender("female");
          msg = "¡Claro! Cambiando la voz a femenina.";
        }
      }
      setResponse(msg);
      setTranscript("");
      setState("idle");
      speak(msg, () => cmdFn.current?.());
      return;
    }

    const redoMatch = text.match(/vuelv(e|a)\s+(a\s+)?(rellenar|escribir|poner|ingresar|cambiar|corregir|rectificar)\s+(el\s+|la\s+|el campo\s+|el dato\s+)?(.+)/i);
    if (redoMatch && session && !session.completed && !session.cancelled) {
      const fieldRef = redoMatch[5].toLowerCase().trim();
      const fieldMap = {
        nombre: "first_name", nombres: "first_name", "nombre completo": "first_name",
        apellido: "last_name", apellidos: "last_name", "apellido paterno": "last_name",
        dni: "document_number", numero: "document_number", documento: "document_number", "numero de documento": "document_number",
        telefono: "phone", celular: "phone", "numero de telefono": "phone", "numero de celular": "phone",
        email: "email", correo: "email", "correo electronico": "email",
        fecha: "birth_date", "fecha de nacimiento": "birth_date", cumpleaños: "birth_date", nacimiento: "birth_date",
        sexo: "gender", genero: "gender",
      };
      const targetName = fieldMap[fieldRef] || session.fields.find(f => f.label.toLowerCase().includes(fieldRef))?.name;
      if (targetName) {
        const targetIdx = session.fields.findIndex(f => f.name === targetName);
        if (targetIdx >= 0) {
          resetField(targetName);
          const question = `Por favor, dame nuevamente ${session.fields[targetIdx].label.toLowerCase()}.`;
          setResponse(question);
          setTranscript("");
          setState("idle");
          speak(question, () => cmdFn.current?.());
          return;
        }
      }
    }

    const cleanActive = text.toLowerCase().trim();

    const isGlobalCommand =
      /^(crear|agendar|registrar|ver|mostrar|cancelar|continuar|retomar)/i.test(cleanActive) &&
      /(cita|médico|medico|paciente|ticket|registro)/i.test(cleanActive);

    if (
      session &&
      !session.completed &&
      !session.cancelled &&
      isGlobalCommand
    ) {
      cancelFilling();

      setResponse("Detecté una nueva orden. Cancelé el llenado anterior y continuaré con tu solicitud.");
      setTranscript("");
      setState("idle");

      setTimeout(() => {
        processInputRef.current?.(text);
      }, 300);

      return;
    }

    if (awaitingFinalConfirmation.current) {
  const clean = text.toLowerCase().trim();

  if (/\b(si|sí|confirmo|guardar|correcto|ok|dale)\b/i.test(clean)) {
    awaitingFinalConfirmation.current = false;
    submitForm();
    return;
  }

  if (/\b(no|cancelar|anular|descartar)\b/i.test(clean)) {
    awaitingFinalConfirmation.current = false;
    cancelFilling();

    const msg = "Registro cancelado. No se guardó la información.";
    setResponse(msg);
    setTranscript("");
    speak(msg, () => cmdFn.current?.());
    return;
  }

  if (isCorrectionIntent(text)) {
    awaitingFinalConfirmation.current = false;
  } else {
    const msg = "Necesito que confirmes: sí para guardar, no para cancelar, o dime qué campo corregir.";
    setResponse(msg);
    setTranscript("");
    speak(msg, () => cmdFn.current?.());
    return;
  }
}

    if (session && !session.completed && !session.cancelled && isCorrectionIntent(text)) {
      const targetField = correctionTargetField(session);

      if (targetField) {
        const targetIdx = session.fields.findIndex(f => f.name === targetField.name);

        if (targetIdx >= 0) {
          correctionHistory.current.push({
          field: targetField.name,
          previous: session.values?.[targetField.name] || "",
          corrected: null,
          date: new Date().toISOString(),
        });
        
          resetField(targetField.name);
          setFieldIndex(targetIdx);

          const question = `Entiendo, vamos a corregir ${targetField.label.toLowerCase()}. Dímelo nuevamente completo.`;
          setResponse(question);
          setTranscript("");
          setState("idle");
          speak(question, () => cmdFn.current?.());
          return;
        }
      }
    }
    if (session && !session.completed && !session.cancelled && session.currentFieldIndex < session.fields.length) {
      await handleFieldValue(text);
      return;
    }

    setTranscript(text);
    setState("processing");
    try {
      const res = await api.post("/assistant/chat", { text });
      const data = res.data || {};
      const msg = data.message || "";
      const tgt = data.target || "";
      const action = data.action || data.intent || "";

      if (data.type === "voice_change") {
        const gender = data.voice === "female" ? "female" : "male";
        setVoiceGender(gender);
        setResponse(msg);
        setState("idle");
        speak(msg, () => cmdFn.current?.());
        return;
      }

      if (data.type === "prefill" && data.prefill) {
        const raw = data.risk_data || null;
        if (raw) {
          setRiskData({
            edad_paciente: raw.patient_age ?? "",
            genero: toGenderSelect(raw.gender),
            especialidad: raw.specialty ?? "",
            prioridad: raw.priority ?? "",
            turno_cita: raw.appointment_shift ?? "",
            conteo_inasistencias_previas: raw.previous_no_show_count ?? "",
            distancia_km: raw.distance_km ?? "",
            dias_hasta_cita: raw.days_until_appointment ?? "",
            minutos_espera_estimados: raw.waiting_minutes_estimated ?? "",
          });
        } else {
          setRiskData(null);
        }
        chainRef.current = data.chain || null;
        if (SIMPLE_CREATE.has(action)) {
          const started = await startCreateFlow(action, data.prefill);
          if (started) return;
        }
        if (data.target && setActivePage) setActivePage(data.target);
        if (onAction) onAction();
        try {
          const entityConfig = {
            agendar_cita: "appointment", crear_paciente: "patient", crear_medico: "doctor",
            actualizar_paciente: "patient", actualizar_medico: "doctor",
          };
          const entity = entityConfig[action] || "appointment";
          const schemaRes = await api.get(`/assistant/form-schema/${entity}`);
          const fields = schemaRes.data?.fields || [];
          startFilling(entity, fields, data.prefill);
        } catch {
          const fallback = { crear_paciente: "patient", crear_medico: "doctor" };
          startFilling(fallback[action] || "appointment", [], data.prefill);
        }
        setTimeout(() => completeFilling(), 100);
        log(`prefill: ${JSON.stringify(data.prefill).slice(0, 80)}`);
        setState("idle");
        setResponse(data.message || msg);
        speak(msg, () => cmdFn.current?.());
        return;
      }

      if (SIMPLE_CREATE.has(action) && data.type !== "success" && data.type !== "error") {
        const started = await startCreateFlow(action, data.prefill);
        if (started) return;
      }

      log(`chat: "${msg.slice(0, 60)}"`);
      setResponse(msg);
      if (tgt && setActivePage) setActivePage(tgt);
      if (onAction && tgt) onAction();
      if (data.ticket) {
        generateTicketPdf(data.ticket).catch((e) => log("err ticket pdf: " + e.message));
      }
      setState("idle");
      speak(msg, () => cmdFn.current?.());
    } catch (e) {
      log(`err: ${e.message}`);
      setBrowserError("Error de conexión.");
      setState("idle");
      setTimeout(() => { setBrowserError(""); cmdFn.current?.(); }, 3000);
    }
  }, [session, handleFieldValue, startCreateFlow, speak, setActivePage, onAction, log, toggleDisabled, resumeFilling]);

  useEffect(() => { processInputRef.current = processInput; }, [processInput]);

  // ─── Wake word ──────────────────────────────────────────────────
  const startWake = () => {
    if (!ar.current) return;
    if (wr.current) { try { wr.current.stop(); } catch (_) {} wr.current = null; }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      log("SpeechRecognition NO disponible");
      if (!warnShown.current) { warnShown.current = true; setBrowserError("Tu navegador no soporta reconocimiento de voz. Usa Chrome."); }
      return;
    }
    const rec = new SR();
    rec.lang = "es-PE";
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript.toLowerCase().trim();
        log(`oyó: "${t}"`);

        if (disabledRef.current) {
          if (isWake(t) && !wokeRef.current) {
            wokeRef.current = true;
            rec.stop();
            toggleDisabled(false);
            setTimeout(() => {
              if (ar.current) wakeFn.current?.();
            }, 100);
          }
          continue;
        }

        if (isWake(t) && !wokeRef.current) {
          wokeRef.current = true;
          wakeCount.current++;
          log(`WAKE #${wakeCount.current}: "${t}"`);
          fullRef.current = true;
          rec.stop();
          setView("mini");
          setState("greeting");
          const msg = "¡Hola Admin! Soy La IA. ¿En qué puedo ayudarte?";
          setResponse(msg);
          if (ttsEnabled) speak(msg, () => cmdFn.current?.());
          else setTimeout(() => cmdFn.current?.(), 800);
          return;
        }
      }
    };
    rec.onend = () => { if (ar.current && !fullRef.current) startWake(); };
    rec.onerror = () => { if (ar.current && !fullRef.current && !disabledRef.current) setTimeout(() => startWake(), 1000); };
    wr.current = rec;
    try { rec.start(); log("wake iniciado"); } catch (e) { log(`wake start err: ${e.message}`); }
  };

  // ─── Escucha comandos (continuo + silencio) ─────────────────────
  const startCmdListen = () => {
    if (!ar.current || disabledRef.current) return;
    if (cr.current) { try { cr.current.stop(); } catch (_) {} cr.current = null; }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    setState("listening");
    const rec = new SR();
    rec.lang = "es-PE";
    rec.continuous = true;
    rec.interimResults = true;
    let accumulated = "";
    let silenceTimer = null;
    const SILENCE_MS = 1200;
    rec.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          accumulated += " " + event.results[i][0].transcript.trim();
        }
      }
      clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {
        rec.stop();
      }, SILENCE_MS);
    };
    rec.onend = () => {
      clearTimeout(silenceTimer);
      const t = accumulated.trim();
      accumulated = "";
      if (t) {
        log(`cmd: "${t.slice(0, 80)}" (${t.length} chars)`);
        processInput(t);
      } else {
        if (state === "listening") setState("idle");
        cmdFn.current?.();
      }
    };
    rec.onerror = () => { setState("idle"); };
    cr.current = rec;
    try { rec.start(); } catch (e) { log(`cmd start err: ${e.message}`); }
  };

  useEffect(() => {
    wakeFn.current = startWake;
    cmdFn.current = startCmdListen;
  });

  useEffect(() => {
    ar.current = true;
    console.log("[LaIA] mounted");
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) console.log("[LaIA] SpeechRecognition NO disponible");
    else console.log("[LaIA] SpeechRecognition disponible");
    const t = setTimeout(() => wakeFn.current?.(), 1500);
    return () => {
      ar.current = false;
      clearTimeout(t);
      wr.current?.stop();
      cr.current?.stop();
      window.speechSynthesis?.cancel();
    };
  }, []);

  async function sendText() {
    const t = textInput.trim();
    if (!t) return;
    setTextInput(""); setShowTextInput(false);
    await processInput(t);
  }

  function close() {
    wr.current?.stop();
    cr.current?.stop();
    window.speechSynthesis?.cancel();
    fullRef.current = false;
    wokeRef.current = false;
    cancelFilling();
    setView("badge"); setState("idle"); setTranscript(""); setResponse(""); setBrowserError("");
    if (!disabledRef.current) setTimeout(() => { if (ar.current) wakeFn.current?.(); }, 500);
  }

  const listening = state === "listening";
  const fillingActive = session && !session.completed && !session.cancelled;

  const fieldIndicator = fillingActive && session.currentFieldIndex < session.fields.length
    ? `Campo ${session.currentFieldIndex + 1}/${session.fields.length}`
    : "";

  const sectionLabel = fillingActive
    ? { patient: "Paciente", doctor: "Médico", appointment: "Cita" }[session.entity] || ""
    : "";

  const progressPct = fillingActive && session.fields.length > 0
    ? Math.round((session.currentFieldIndex / session.fields.length) * 100) : 0;

  if (disabled) {
    return (
      <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2 bg-gray-800/70 backdrop-blur rounded-full px-4 py-2 shadow-lg border border-gray-600/30">
        <div className="w-6 h-6 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-bold">LA</div>
        <span className="text-gray-400 text-[10px] font-light tracking-wide whitespace-nowrap">La IA desactivada</span>
        <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
        <button onClick={() => toggleDisabled(false)} className="text-gray-400 hover:text-white ml-1" title="Reactivar">
          <Power size={12} />
        </button>
      </div>
    );
  }

  return (
    <>
      {view === "badge" && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2 bg-blue-900/70 backdrop-blur rounded-full px-4 py-2 shadow-lg border border-blue-400/30">
          <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold">LA</div>
          <span className="text-white/60 text-[10px] font-light tracking-wide whitespace-nowrap">Di "Eva Salud" o "La IA"</span>
          <div className={`w-1.5 h-1.5 rounded-full ${browserError ? 'bg-red-400' : 'bg-green-400'} animate-pulse`} />
          <button onClick={() => toggleDisabled(true)} className="text-white/40 hover:text-white/80 ml-1" title="Desactivar">
            <PowerOff size={10} />
          </button>
        </div>
      )}

      {(view === "mini" || view === "full") && (
        view === "mini" ? (
          <div className="fixed bottom-5 right-5 z-50 max-w-sm w-[340px] bg-blue-950/85 backdrop-blur-xl rounded-2xl shadow-2xl border border-blue-400/30 p-4 flex flex-col items-center gap-3">
            <div className="flex items-center justify-between w-full">
              <span className="text-white/40 text-[9px]">Asistente La IA</span>
              <button onClick={() => toggleDisabled(true)} className="text-white/30 hover:text-white/60 p-1" title="Desactivar">
                <PowerOff size={12} />
              </button>
            </div>
            <div className={`w-16 h-16 rounded-full transition-all duration-700 flex items-center justify-center shadow-lg ${
              state === "listening" ? "bg-gradient-to-br from-green-400 to-emerald-600 shadow-green-400/50 animate-pulse scale-110" :
              state === "processing" ? "bg-gradient-to-br from-purple-400 to-indigo-600 shadow-purple-400/50 scale-105" :
              state === "speaking" ? "bg-gradient-to-br from-emerald-400 to-teal-600 shadow-emerald-400/50 scale-105" :
              state === "greeting" ? "bg-gradient-to-br from-yellow-400 to-orange-500 shadow-yellow-400/50 scale-110" :
              "bg-gradient-to-br from-blue-400 to-blue-800 shadow-blue-500/30"
            }`}>
              {state === "processing" ? (
                <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              ) : (
                <img src={LA_IA_AVATAR} alt="La IA" className="w-10 h-10 rounded-full" />
              )}
            </div>
            <span className="text-white/60 text-[10px] font-light tracking-[0.2em] uppercase">
              {state === "listening" && "Escuchando..."}
              {state === "processing" && "Procesando..."}
              {state === "speaking" && "Hablando..."}
              {state === "greeting" && "¡Bienvenido!"}
              {state === "idle" && (fillingActive ? `${sectionLabel}: ${fieldIndicator}` : "Asistente La IA")}
            </span>

            {fillingActive && (
              <div className="w-full bg-blue-900/30 rounded-full h-1.5">
                <div className="bg-green-400 h-1.5 rounded-full transition-all duration-300" style={{ width: `${progressPct}%` }} />
              </div>
            )}

            {browserError && (
              <div className="bg-red-900/80 backdrop-blur rounded-xl px-4 py-3 w-full border-2 border-red-400/60 text-center">
                <p className="text-red-200 text-sm font-bold mb-1">Error</p>
                <p className="text-red-300 text-xs">{browserError}</p>
              </div>
            )}
            {transcript && (
              <div className="bg-white/10 backdrop-blur rounded-xl px-4 py-2 w-full text-center">
                <p className="text-white/50 text-[10px] uppercase tracking-wider mb-0.5">Tú</p>
                <p className="text-white text-sm">{transcript}</p>
              </div>
            )}
            {response && (
              <div className="bg-blue-900/40 backdrop-blur rounded-xl px-4 py-2 w-full border border-blue-500/20 max-h-36 overflow-y-auto">
                <p className="text-blue-300 text-[10px] uppercase tracking-wider mb-0.5">La IA</p>
                <p className="text-white/90 text-sm leading-relaxed whitespace-pre-wrap">{response}</p>
              </div>
            )}
            <div className="flex items-center gap-3 mt-1">
              {listening && (
                <div className="text-green-400 text-xs flex items-center gap-1.5 bg-green-900/30 px-3 py-1.5 rounded-full">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-ping" />
                  Grabando
                </div>
              )}
              <button onClick={() => { setShowTextInput(!showTextInput); setTextInput(""); }}
                className="bg-white/10 hover:bg-white/20 text-white p-2 rounded-full transition" title="Escribir">
                <Keyboard size={16} />
              </button>
              <button onClick={() => setTtsEnabled(!ttsEnabled)}
                className={`p-2 rounded-full transition ${ttsEnabled ? "bg-white/20 text-white" : "bg-white/10 text-white/50"}`}>
                {ttsEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
              </button>
              <button onClick={() => setShowDebug(!showDebug)}
                className="bg-white/10 hover:bg-white/20 text-white p-2 rounded-full transition" title="Debug">
                <Bug size={16} />
              </button>
              <button onClick={() => setView("full")}
                className="bg-white/10 hover:bg-white/20 text-white p-2 rounded-full transition" title="Expandir">
                <Maximize2 size={16} />
              </button>
              <button onClick={close}
                className="bg-red-500/80 hover:bg-red-500 text-white p-2 rounded-full transition">
                <X size={16} />
              </button>
            </div>
            {showTextInput && (
              <div className="flex gap-2 w-full">
                <input value={textInput} onChange={(e) => setTextInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendText()}
                  placeholder={fillingActive ? "Responde el campo..." : "Escribe..."}
                  className="flex-1 bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-white text-xs placeholder-white/40 focus:outline-none focus:border-blue-400" autoFocus />
                <button onClick={sendText} className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-lg text-xs transition">Enviar</button>
              </div>
            )}
            {showDebug && (
              <div className="bg-gray-900/90 rounded-xl px-3 py-2 w-full border border-gray-600 max-h-32 overflow-y-auto font-mono">
                {debugLog.map((l, i) => <p key={i} className="text-gray-300 text-[9px] leading-relaxed">{l}</p>)}
              </div>
            )}
          </div>
        ) : (
          <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm">
            <div className="relative flex flex-col items-center gap-5 w-full max-w-md px-6">
              <div className={`w-32 h-32 rounded-full transition-all duration-700 flex items-center justify-center shadow-2xl ${
                state === "listening" ? "bg-gradient-to-br from-green-400 to-emerald-600 shadow-green-400/50 animate-pulse scale-110" :
                state === "processing" ? "bg-gradient-to-br from-purple-400 to-indigo-600 shadow-purple-400/50 scale-105" :
                state === "speaking" ? "bg-gradient-to-br from-emerald-400 to-teal-600 shadow-emerald-400/50 scale-105" :
                state === "greeting" ? "bg-gradient-to-br from-yellow-400 to-orange-500 shadow-yellow-400/50 scale-110" :
                "bg-gradient-to-br from-blue-400 to-blue-800 shadow-blue-500/30"
              }`}>
                {state === "processing" ? (
                  <div className="w-8 h-8 border-3 border-white/40 border-t-white rounded-full animate-spin" />
                ) : (
                  <img src={LA_IA_AVATAR} alt="La IA" className="w-16 h-16 rounded-full" />
                )}
              </div>
              <span className="text-white/60 text-xs font-light tracking-[0.2em] uppercase">
                {state === "listening" && "Escuchando..."}
                {state === "processing" && "Procesando..."}
                {state === "speaking" && "Hablando..."}
                {state === "greeting" && "¡Bienvenido!"}
                {state === "idle" && (fillingActive ? `${sectionLabel}: ${fieldIndicator}` : "Asistente La IA")}
              </span>

              {fillingActive && (
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div className="bg-green-400 h-2 rounded-full transition-all duration-300" style={{ width: `${progressPct}%` }} />
                </div>
              )}

              {browserError && (
                <div className="bg-red-900/80 backdrop-blur rounded-xl px-5 py-4 w-full border-2 border-red-400/60 text-center">
                  <p className="text-red-200 text-sm font-bold mb-1">Error</p>
                  <p className="text-red-300 text-sm">{browserError}</p>
                </div>
              )}
              {transcript && (
                <div className="bg-white/10 backdrop-blur rounded-xl px-5 py-3 w-full text-center">
                  <p className="text-white/50 text-xs uppercase tracking-wider mb-1">Tú</p>
                  <p className="text-white text-base">{transcript}</p>
                </div>
              )}
              {response && (
                <div className="bg-blue-900/40 backdrop-blur rounded-xl px-5 py-3 w-full border border-blue-500/20 max-h-60 overflow-y-auto">
                  <p className="text-blue-300 text-xs uppercase tracking-wider mb-1">La IA</p>
                  <p className="text-white/90 text-base leading-relaxed whitespace-pre-wrap">{response}</p>
                </div>
              )}
              <div className="flex items-center gap-3 mt-2">
                {listening && (
                  <div className="text-green-400 text-xs flex items-center gap-1.5 bg-green-900/30 px-3 py-1.5 rounded-full">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-ping" />
                    Grabando
                  </div>
                )}
                <button onClick={() => { setShowTextInput(!showTextInput); setTextInput(""); }}
                  className="bg-white/10 hover:bg-white/20 text-white p-2.5 rounded-full transition" title="Escribir">
                  <Keyboard size={18} />
                </button>
                <button onClick={() => setTtsEnabled(!ttsEnabled)}
                  className={`p-2.5 rounded-full transition ${ttsEnabled ? "bg-white/20 text-white" : "bg-white/10 text-white/50"}`}>
                  {ttsEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
                </button>
                <button onClick={() => setShowDebug(!showDebug)}
                  className="bg-white/10 hover:bg-white/20 text-white p-2.5 rounded-full transition" title="Debug">
                  <Bug size={18} />
                </button>
                <button onClick={() => setView("mini")}
                  className="bg-white/10 hover:bg-white/20 text-white p-2.5 rounded-full transition" title="Minimizar">
                  <Minimize2 size={18} />
                </button>
                <button onClick={() => toggleDisabled(true)}
                  className="bg-white/10 hover:bg-white/20 text-white p-2.5 rounded-full transition" title="Desactivar">
                  <PowerOff size={18} />
                </button>
                <button onClick={close}
                  className="bg-red-500/80 hover:bg-red-500 text-white p-2.5 rounded-full transition">
                  <X size={18} />
                </button>
              </div>
              {showTextInput && (
                <div className="flex gap-2 w-full">
                  <input value={textInput} onChange={(e) => setTextInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendText()}
                    placeholder={fillingActive ? "Responde el campo..." : "Escribe..."}
                    className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white text-sm placeholder-white/40 focus:outline-none focus:border-blue-400" autoFocus />
                  <button onClick={sendText} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm transition">Enviar</button>
                </div>
              )}
              {showDebug && (
                <div className="bg-gray-900/90 rounded-xl px-4 py-3 w-full border border-gray-600 max-h-48 overflow-y-auto font-mono">
                  {debugLog.map((l, i) => <p key={i} className="text-gray-300 text-[10px] leading-relaxed">{l}</p>)}
                </div>
              )}
            </div>
          </div>
        )
      )}
    </>
  );
}

export default LaIA;
