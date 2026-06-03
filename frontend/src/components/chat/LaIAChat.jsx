import { useState, useRef, useEffect, useCallback } from "react";
import { Bot, MessageCircle, Send, X, Mic, MicOff, Volume2, VolumeX, Sparkles, PowerOff } from "lucide-react";
import api from "../../services/api";
import { getUserName } from "../../modules/auth/sessionService";
import { useFormFilling } from "../../context/FormFillingContext";

const LA_IA_AVATAR = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='48' fill='%231e3a5f'/%3E%3Ctext x='50' y='62' font-size='32' text-anchor='middle' fill='white' font-family='Arial'%3ELA%3C/text%3E%3C/svg%3E";

// ─── Normalizadores de entrada de voz ───────────────────────────────────────

function normalizeEmail(raw) {
  let v = raw.toLowerCase().trim();

  // Limpiar prefijos: "correo:", "mi correo es", "email:", etc.
  v = v.replace(/^(?:mi\s+|el\s+|la\s+)?(?:correo|email|correo\s+electronico|correo\s+electrónico)\s*(?::\s*)?(?:\s+es\s+)?/i, "");

  v = v.replace(/\barroba\b/g, "@");
  v = v.replace(/\barrobe\b/g, "@");
  v = v.replace(/\barroba\b/g, "@");
  v = v.replace(/\barova\b/g, "@");
  v = v.replace(/\barroa\b/g, "@");
  v = v.replace(/\ba\s*rroba\b/g, "@");
  v = v.replace(/\ba\s*arroba\b/g, "@");
  v = v.replace(/\b\s*en\s*(?=[a-z]+\s*(?:punto|dot|\.|com|es|pe))\b/g, "@");
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

  // Extraer solo email del texto
  const emailMatch = v.match(/[a-zA-Z0-9._%+\-À-ÿ]+@[a-zA-Z0-9.\-À-ÿ]+\.[a-zA-ZÀ-ÿ]{2,}/);
  if (emailMatch) return emailMatch[0];

  v = v.replace(/\s+/g, "");

  // Eliminar acentos (Chávez → Chavez)
  v = v.replace(/[áäà]/g, "a").replace(/[éëè]/g, "e").replace(/[íïì]/g, "i")
       .replace(/[óöò]/g, "o").replace(/[úüù]/g, "u").replace(/ñ/g, "n");

  return v;
}

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

function parseSpanishYear(text) {
  const words = text.toLowerCase().split(/\s+/);
  let total = 0, current = 0;
  for (const w of words) {
    const n = parseSpanishNumber(w);
    if (n === null) continue;
    if (n >= 1000) { current = Math.max(current, 1) * n; total += current; current = 0; }
    else if (n >= 100) { current = Math.max(current, 1) * n; }
    else { current += n; }
  }
  total += current;
  return total > 0 ? total : null;
}

const WEEKDAYS_ES = {
  lunes: 1, martes: 2, miercoles: 3, miércoles: 3,
  jueves: 4, viernes: 5, sabado: 6, sábado: 6, domingo: 0,
};

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
  const isoMatch = v.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (isoMatch) { const [, y, m, d] = isoMatch; return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`; }
  const dmyMatch = v.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$/);
  if (dmyMatch) { let [, d, m, y] = dmyMatch; if (y.length === 2) y = "20" + y; return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`; }

  for (const [dayName, dayNum] of Object.entries(WEEKDAYS_ES)) {
    if (v.includes(dayName)) {
      const nextDate = getNextWeekday(dayNum);
      return `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, "0")}-${String(nextDate.getDate()).padStart(2, "0")}`;
    }
  }

  if (/\bhoy\b/.test(v)) { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }
  if (/\b(?:mañana|manana)\b/.test(v)) { const d = new Date(); d.setDate(d.getDate() + 1); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }
  if (/\b(?:pasado\s*mañana|pasado\s*manana)\b/.test(v)) { const d = new Date(); d.setDate(d.getDate() + 2); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }
  if (/\b(?:pr[oó]xima\s*semana|semana\s*que\s*viene)\b/.test(v)) { const d = new Date(); d.setDate(d.getDate() + 7); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }

  let day = null, month = null, year = null;
  const y4 = v.match(/\b(\d{4})\b/);
  const y2 = v.match(/\b(\d{2})\b\s*$/);
  if (y4) { year = parseInt(y4[1]); }
  else if (y2) { year = parseInt(y2[1]); if (year >= 0 && year <= 49) year += 2000; else if (year >= 50 && year <= 99) year += 1900; }
  else { const yWords = v.match(/((?:\w+\s+){0,2}mil\s+(?:\w+\s+)*\w+)/); if (yWords) year = parseSpanishYear(yWords[1]); }
  for (const [name, num] of Object.entries(MONTHS_ES)) { if (v.includes(name)) { month = num; break; } }
  const dayDigits = v.match(/(?:día|dia)\s+(\d{1,2})|(\b\d{1,2}\b)(?=\s*de\s+)/);
  if (dayDigits) { day = parseInt(dayDigits[1] || dayDigits[2]); }
  else {
    const dayWords = v.match(/\b(uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciseis|diecisiete|dieciocho|diecinueve|veinte|veintiuno|veintidos|veintitres|veinticuatro|veinticinco|veintiseis|veintisiete|veintiocho|veintinueve|treinta)\b/);
    if (dayWords) day = parseSpanishNumber(dayWords[1]) || parseInt(dayWords[1]);
  }
  if (day && month && year) { const d = new Date(year, parseInt(month) - 1, day); if (!isNaN(d.getTime())) return `${year}-${month}-${String(day).padStart(2, "0")}`; }
  const ts = Date.parse(v);
  if (!isNaN(ts)) { const d = new Date(ts); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }
  return raw;
}

function normalizeFieldValue(field, raw) {
  if (!raw || typeof raw !== "string") return raw;
  const trimmed = raw.trim();
  if (field.type === "email" || field.name === "email") return normalizeEmail(trimmed);
  if (field.name === "birth_date" || field.type === "date" || field.type === "datetime-local") return parseSpanishDate(trimmed);
  return trimmed;
}

// ─── Fin normalizadores ─────────────────────────────────────────────────────

const CREATE_ACTIONS = new Set(["crear_paciente", "crear_medico", "agendar_cita"]);
const SIMPLE_CREATE = new Set(["crear_paciente", "crear_medico"]);
const DESACTIVAR = ["desactivate", "desactivar", "desactivada", "cállate", "callate", "silencio"];
const WAKE = ["ey eva", "hey eva", "eva salud", "la ia", "asistente la ia"];
function isDesactivar(t) { return DESACTIVAR.some(w => t.toLowerCase().includes(w)); }

function LaIAChat() {
  const { session, startFilling, setCurrentValue, nextField, resetField, completeFilling, cancelFilling, getSession } = useFormFilling();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [wakeMode, setWakeMode] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [disabled, setDisabled] = useState(false);
  const bottomRef = useRef(null);
  const recognitionRef = useRef(null);
  const wakeRecognitionRef = useRef(null);
  const userName = useRef(getUserName());
  const initialized = useRef(false);
  const disabledRef = useRef(false);

  const voiceRef = useRef(null);

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
      } else {
        voiceRef.current = null;
      }
    };
    select();
  }, []);

  const speak = useCallback(
    (text, onDone) => {
      if (!ttsEnabled || disabledRef.current) { setTimeout(() => onDone?.(), 100); return; }
      const clean = text.replace(/\*+/g, "").replace(/\n/g, ". ").replace(/\s+/g, " ").trim();
      window.speechSynthesis?.cancel();
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.lang = "es-PE";
      utterance.rate = 1.1;
      utterance.pitch = 1.0;
      if (voiceRef.current) utterance.voice = voiceRef.current;
      utterance.onend = () => setTimeout(() => onDone?.(), 300);
      utterance.onerror = () => {};
      window.speechSynthesis.speak(utterance);
    },
    [ttsEnabled],
  );

  // ─── Inicializar saludo ───────────────────────────────────────
  useEffect(() => {
    if (open && !initialized.current) {
      initialized.current = true;
      setMessages([
        {
          role: "bot",
          text: `¡Hola **${userName.current}**! Soy **La IA**, tu asistente inteligente.\n\nPuedes *escribirme* o *hablarme*. Di **"Eva Salud"** o **"La IA"** para activar mi voz 🎤`,
        },
      ]);
    }
  }, [open]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ─── Web Speech: crear reconocimiento ──────────────────────────
  const createRecognition = (onResult, onEnd, continuous = false) => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const rec = new SR();
    rec.lang = "es-PE";
    rec.continuous = continuous;
    rec.interimResults = continuous;
    rec.onresult = onResult;
    rec.onend = onEnd;
    rec.onerror = () => {};
    return rec;
  };

  // ─── Escucha continua para wake word ───────────────────────────
  const startWakeListening = useCallback(() => {
    const rec = createRecognition(
      (event) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript.toLowerCase().trim();
          if (WAKE.some(w => transcript.includes(w))) {
            rec.stop();
            setWakeMode(false);
            setVoiceMode(true);
            setMessages((prev) => [
              ...prev,
              { role: "bot", text: `¡Aquí estoy **${userName.current}**! Dime en qué te ayudo 🎤`, sub: true },
            ]);
            speak(`Aquí estoy ${userName.current}, dime en qué te ayudo`);
            setTimeout(() => startVoiceCapture(), 500);
          }
        }
      },
      () => {
        if (wakeMode && !disabledRef.current) startWakeListening();
      },
      true,
    );
    if (rec) {
      wakeRecognitionRef.current = rec;
      rec.start();
    }
  }, [wakeMode, speak]);

  // ─── Capturar voz del usuario ──────────────────────────────────
  const startVoiceCapture = () => {
    setListening(true);
    const rec = createRecognition(
      (event) => {
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          }
        }
        if (final) {
          rec.stop();
          setListening(false);
          setInput(final);
          setTimeout(() => sendMessage(final), 200);
        }
      },
      () => {
        setListening(false);
        if (voiceMode && !disabledRef.current) startVoiceCapture();
      },
      false,
    );
    if (rec) {
      recognitionRef.current = rec;
      rec.start();
    }
  };

  // ─── Activar/desactivar modo voz ───────────────────────────────
  const toggleVoiceMode = () => {
    if (disabledRef.current) return;
    if (voiceMode) {
      setVoiceMode(false);
      setListening(false);
      wakeRecognitionRef.current?.stop();
      recognitionRef.current?.stop();
      window.speechSynthesis?.cancel();
    } else {
      setVoiceMode(true);
      setWakeMode(true);
      startWakeListening();
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: `Escuchando... Di **"Eva Salud"** o **"La IA"** para activarme 🎤`, sub: true },
      ]);
    }
  };

  // ─── Llenar campo actual ───────────────────────────────────────
  const handleFieldValue = useCallback(async (rawValue) => {
    const s = getSession();
    if (!s || s.completed || s.cancelled) return false;

    const fields = s.fields;
    const idx = s.currentFieldIndex;
    if (idx >= fields.length) return false;

    const field = fields[idx];
    let value = normalizeFieldValue(field, rawValue);

    // Limpieza básica para números hablados
    if (field.name === "document_number" || field.name === "dni" || field.name === "phone" || field.name === "telefono") {
      value = String(value).replace(/\D/g, "");
    }

    // Regla crítica: médico se llena CAMPO POR CAMPO.
    // No dividir "Diego Luis" en nombre/apellido automáticamente.
    if (s.entity === "doctor" && field.name === "first_name") {
      if (String(value).includes("@") || /\.com|\.pe|gmail|hotmail|outlook/i.test(String(value))) {
        const question = "Ese dato parece un correo. Ahora necesito solo los nombres del médico. Ejemplo: Diego Luis.";
        setMessages((prev) => [...prev, { role: "bot", text: question }]);
        speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
        return true;
      }
    }

    if (s.entity === "doctor" && field.name === "last_name") {
      if (String(value).includes("@") || /\.com|\.pe|gmail|hotmail|outlook/i.test(String(value))) {
        const question = "Ese dato parece un correo. Ahora necesito solo los apellidos del médico. Ejemplo: Quispe Mamani.";
        setMessages((prev) => [...prev, { role: "bot", text: question }]);
        speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
        return true;
      }
    }

    // Validación general: nombres/apellidos no deben ser correo
    if (
      (field.name === "first_name" || field.name === "last_name") &&
      (String(value).includes("@") || /\.com|\.pe|gmail|hotmail|outlook/i.test(String(value)))
    ) {
      const question = `Ese dato parece un correo. Ahora necesito ${field.label.toLowerCase()}, no correo.`;
      setMessages((prev) => [...prev, { role: "bot", text: question }]);
      speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
      return true;
    }

    // Validación email
    if (field.name === "email" || field.type === "email") {
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(String(value))) {
        const question = "Correo inválido. Dímelo así: usuario arroba gmail punto com.";
        setMessages((prev) => [...prev, { role: "bot", text: question }]);
        speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
        return true;
      }
    }

    // Validación DNI exacto
    if (field.name === "document_number" || field.name === "dni") {
      if (String(value).length !== 8) {
        const question = "El DNI debe tener 8 dígitos. Repítelo número por número.";
        setMessages((prev) => [...prev, { role: "bot", text: question }]);
        speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
        return true;
      }
    }

    // Validación teléfono exacto
    if (field.name === "phone" || field.name === "telefono") {
      const digits = String(value).replace(/\D/g, "");
      if (digits.length !== 9 || !digits.startsWith("9")) {
        const question = "El teléfono debe tener 9 dígitos y empezar con 9. Ejemplo: 918512301.";
        setMessages((prev) => [...prev, { role: "bot", text: question }]);
        speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
        return true;
      }
    }

    // Validar fecha de cita no sea pasada
    if ((field.name === "scheduled_at" || field.type === "datetime-local") && new Date(value) < new Date()) {
      const question = "La fecha de la cita no puede ser en el pasado. Dime una fecha y hora futura.";
      setMessages((prev) => [...prev, { role: "bot", text: question }]);
      speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
      return true;
    }

    // Normalizar especialidad mal escuchada por voz
    if (field.name === "specialty") {
      const v = String(value).toLowerCase().trim();
      if (["tvc", "tb c", "tbc", "tebecé", "te be ce", "te ve ce", "pvc"].includes(v)) {
        value = "TBC";
      }
    }

    setCurrentValue(field.name, value);
    setMessages((prev) => [...prev, { role: "bot", text: `✏️ **${field.label}**: ${value}`, sub: true }]);

    const nextIdx = idx + 1;
    if (nextIdx >= fields.length) {
      completeFilling();
      const msg = "Todos los datos están completos. Guardando...";
      setMessages((prev) => [...prev, { role: "bot", text: msg, sub: true }]);
      speak(msg, () => submitForm());
    } else {
      const nextField = fields[nextIdx];
      const question = `¿Cuál es ${nextField.label.toLowerCase()}?`;
      setMessages((prev) => [...prev, { role: "bot", text: question }]);
      speak(question, () => {
        if (voiceMode) setTimeout(() => startVoiceCapture(), 500);
      });
    }

    return true;
  }, [getSession, setCurrentValue, completeFilling, speak, voiceMode]);

  // ─── Enviar formulario completo ─────────────────────────────────
  const submitForm = useCallback(async () => {
    const s = getSession();
    if (!s) return;
    const vals = s.values;
    const entity = s.entity;
    setLoading(true);
    try {
      const res = await api.post("/assistant/form-submit", { entity, data: vals });
      const data = res.data;
      if (data.type === "error") {
        cancelFilling();
        setMessages((prev) => [...prev, { role: "bot", text: data.message || "Error al guardar.", type: "error" }]);
        speak(data.voice || "Error al guardar.", () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
        return;
      }
      const msg = data.message || "Registrado correctamente.";
      setMessages((prev) => [...prev, { role: "bot", text: `✅ ${msg}`, type: "success" }]);
      cancelFilling();
      speak(data.voice || msg, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 422 && Array.isArray(detail)) {
        const getLoc = (d) => { const loc = d.loc || []; return loc[loc.length - 1]; };
        const badField = detail.map(getLoc).filter(Boolean)[0];
        if (badField && s.fields.some(f => f.name === badField)) {
          const field = s.fields.find(f => f.name === badField);
          const errMsg = detail.find(d => getLoc(d) === badField)?.msg || "dato inválido";
          cancelFilling();
          startFilling(s.entity, s.fields, { ...s.values });
          const s2 = getSession();
          if (s2 && s2.fields.length > 0) {
            setTimeout(() => {
              const question = `El **${field.label.toLowerCase()}** es incorrecto: ${errMsg}. ¿Cuál es ${field.label.toLowerCase()}?`;
              setMessages((prev) => [...prev, { role: "bot", text: `⚠️ ${question}` }]);
              speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
            }, 500);
          }
        } else {
          cancelFilling();
          const errText = detail.map(d => d.msg).join(". ");
          setMessages((prev) => [...prev, { role: "bot", text: `Error: ${errText}`, type: "error" }]);
          speak("Error al guardar.", () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
        }
      } else {
        const msg = err.response?.data?.detail || err.response?.data?.message || "Error de conexión.";
        setMessages((prev) => [...prev, { role: "bot", text: `Error: ${typeof msg === "string" ? msg : JSON.stringify(msg)}`, type: "error" }]);
        cancelFilling();
        speak("Error de conexión.", () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
      }
    }
    setLoading(false);
  }, [getSession, cancelFilling, startFilling, speak, voiceMode]);

  // ─── Iniciar sesión de llenado ──────────────────────────────────
  const startCreateFlow = useCallback(async (action, prefillData = {}) => {
    const entityMap = { crear_paciente: "patient", crear_medico: "doctor", agendar_cita: "appointment" };
    const entity = entityMap[action];
    if (!entity) return false;
    try {
      const res = await api.get(`/assistant/form-schema/${entity}`);
      const schema = res.data;
      if (schema.error) return false;
      const fields = schema.fields;
      startFilling(entity, fields, prefillData);
      setMessages((prev) => [...prev, { role: "bot", text: `📋 Voy a guiarte paso a paso para completar los datos.` }]);
      const firstUnfilled = fields.find(f => !prefillData[f.name]);
      if (firstUnfilled) {
        const question = `¿Cuál es ${firstUnfilled.label.toLowerCase()}?`;
        setMessages((prev) => [...prev, { role: "bot", text: question }]);
        speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
      }
      return true;
    } catch (e) {
      return false;
    }
  }, [startFilling, speak, voiceMode]);

  // ─── Enviar mensaje ────────────────────────────────────────
  const sendMessage = async (textOverride) => {
    const text = (textOverride || input).trim();
    if (!text || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);

    if (isDesactivar(text)) {
      disabledRef.current = true;
      setDisabled(true);
      window.speechSynthesis?.cancel();
      setVoiceMode(false);
      setListening(false);
      wakeRecognitionRef.current?.stop();
      recognitionRef.current?.stop();
      setMessages((prev) => [...prev, { role: "bot", text: "🔇 La IA desactivada. Di 'Eva Salud' o escribe para reactivar.", sub: true }]);
      return;
    }

    if (disabledRef.current) {
      if (WAKE.some(w => text.toLowerCase().includes(w))) {
        disabledRef.current = false;
        setDisabled(false);
        setMessages((prev) => [...prev, { role: "bot", text: `¡Hola **${userName.current}**! ¿En qué puedo ayudarte?` }]);
        speak(`Hola ${userName.current}, ¿en qué puedo ayudarte?`);
      } else {
        setMessages((prev) => [...prev, { role: "bot", text: "🔇 Estoy desactivada. Di 'Eva Salud' o 'La IA' para reactivarme.", sub: true }]);
      }
      return;
    }

    const redoMatch = text.match(/vuelv(e|a)\s+(a\s+)?(rellenar|escribir|poner|ingresar|cambiar|corregir|rectificar)\s+(el\s+|la\s+|el campo\s+|el dato\s+)?(.+)/i);
    if (redoMatch) {
      const s2 = getSession();
      if (s2 && !s2.completed && !s2.cancelled) {
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
        const targetName = fieldMap[fieldRef] || s2.fields.find(f => f.label.toLowerCase().includes(fieldRef))?.name;
        if (targetName) {
          const targetIdx = s2.fields.findIndex(f => f.name === targetName);
          if (targetIdx >= 0) {
            resetField(targetName);
            const question = `Por favor, dame nuevamente ${s2.fields[targetIdx].label.toLowerCase()}.`;
            setMessages((prev) => [...prev, { role: "bot", text: question }]);
            speak(question, () => { if (voiceMode) setTimeout(() => startVoiceCapture(), 500); });
            setLoading(false);
            return;
          }
        }
      }
    }

    const s = getSession();
    if (s && !s.completed && !s.cancelled && s.currentFieldIndex < s.fields.length) {
      await handleFieldValue(text);
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/assistant/chat", { text });
      const data = res.data;
      const msg = data.message || "";
      const action = data.action || data.intent || "";

      if (data.type === "voice_change") {
        const gender = data.voice === "female" ? "female" : "male";
        setVoiceGender(gender);
        setMessages((prev) => [...prev, { role: "bot", text: msg }]);
        speak(msg);
        setLoading(false);
        if (voiceMode) setTimeout(() => startVoiceCapture(), 600);
        return;
      }

      if (SIMPLE_CREATE.has(action) && data.type !== "success" && data.type !== "error") {
        setLoading(false);
        const started = await startCreateFlow(action, data.prefill);
        if (started) return;
      }

      setMessages((prev) => [...prev, { role: "bot", text: msg, type: data.type }]);
      if (data.type !== "form" && data.type !== "emergency") speak(msg);

      if (voiceMode) {
        setTimeout(() => startVoiceCapture(), 1000);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "bot", text: "Error de conexión con el servidor.", type: "error" }]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ─── Formatear texto ────────────────────────────────────
  const formatText = (text) => {
    return text
      .split(/(\*[^*]+\*)/g)
      .map((part, i) =>
        part.startsWith("*") && part.endsWith("*") ? (
          <strong key={i} className="font-semibold">{part.slice(1, -1)}</strong>
        ) : (
          part.split("\n").map((line, j) => (
            <span key={`${i}-${j}`}>
              {j > 0 && <br />}
              {line}
            </span>
          ))
        ),
      );
  };

  const fillingActive = session && !session.completed && !session.cancelled;
  const progressPct = fillingActive && session.fields.length > 0
    ? Math.round((session.currentFieldIndex / session.fields.length) * 100) : 0;
  const sectionLabel = fillingActive
    ? { patient: "Paciente", doctor: "Médico", appointment: "Cita" }[session.entity] || ""
    : "";

  const msgStyles = {
    user: "bg-blue-600 text-white self-end rounded-br-sm",
    bot: "bg-gray-100 text-gray-800 self-start rounded-bl-sm",
    emergency: "bg-red-50 text-red-800 border border-red-200 self-start rounded-bl-sm",
    sub: "bg-blue-50 text-blue-600 self-start rounded-bl-sm text-xs italic",
    error: "bg-red-50 text-red-700 self-start rounded-bl-sm border border-red-200",
    success: "bg-green-50 text-green-700 self-start rounded-bl-sm border border-green-200",
  };

  return (
    <>
      {open && (
        <div className="fixed bottom-20 right-4 z-50 w-96 h-[36rem] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">
          {/* ─── Header ──────────────────────────────────── */}
          <div className="bg-blue-900 text-white px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2.5">
              <img src={LA_IA_AVATAR} alt="La IA" className="w-8 h-8 rounded-full" />
              <div>
                <span className="font-semibold text-sm">Asistente La IA</span>
                <span className="text-[10px] text-blue-200 block -mt-0.5">
                  {disabled ? "Desactivada" : voiceMode ? "Modo voz activo 🎤" : "Asistente Inteligente"}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {!disabled && (
                <>
                  <button
                    onClick={toggleVoiceMode}
                    className={`p-1.5 rounded hover:bg-blue-800 ${voiceMode ? "bg-green-700 text-white" : "text-blue-200"}`}
                    title={voiceMode ? "Desactivar voz" : "Activar voz (di 'Eva Salud' o 'La IA')"}
                  >
                    {voiceMode ? <Sparkles size={16} /> : <Mic size={16} />}
                  </button>
                  <button
                    onClick={() => setTtsEnabled(!ttsEnabled)}
                    className={`p-1.5 rounded hover:bg-blue-800 ${ttsEnabled ? "text-white" : "text-blue-300"}`}
                    title={ttsEnabled ? "Silenciar voz" : "Activar voz"}
                  >
                    {ttsEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
                  </button>
                </>
              )}
              <button
                onClick={() => {
                  disabledRef.current = !disabledRef.current;
                  setDisabled(!disabled);
                  window.speechSynthesis?.cancel();
                  if (!disabled) {
                    setVoiceMode(false);
                    setListening(false);
                    wakeRecognitionRef.current?.stop();
                    recognitionRef.current?.stop();
                  }
                }}
                className={`p-1.5 rounded hover:bg-blue-800 ${disabled ? "text-red-300" : "text-blue-200"}`}
                title={disabled ? "Reactivar" : "Desactivar"}
              >
                <PowerOff size={16} />
              </button>
              <button onClick={() => setOpen(false)} className="p-1.5 rounded hover:bg-blue-800">
                <X size={18} />
              </button>
            </div>
          </div>

          {/* ─── Barra de progreso ────────────────────────── */}
          {fillingActive && (
            <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2 shrink-0">
              <div className="flex items-center justify-between text-xs text-yellow-700 mb-1">
                <span>Llenando {sectionLabel}</span>
                <span>{session.currentFieldIndex}/{session.fields.length}</span>
              </div>
              <div className="w-full bg-yellow-200 rounded-full h-1.5">
                <div className="bg-yellow-500 h-1.5 rounded-full transition-all duration-300" style={{ width: `${progressPct}%` }} />
              </div>
            </div>
          )}

          {/* ─── Indicador de escucha ────────────────────── */}
          {listening && (
            <div className="bg-green-50 text-green-700 text-xs text-center py-1.5 flex items-center justify-center gap-2 shrink-0">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-ping" />
              Escuchando... habla ahora
            </div>
          )}
          {wakeMode && !disabled && (
            <div className="bg-blue-50 text-blue-600 text-xs text-center py-1.5 flex items-center justify-center gap-2 shrink-0">
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              Esperando "Eva Salud" o "La IA"...
            </div>
          )}

          {/* ─── Mensajes ────────────────────────────────── */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex items-end gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                {msg.role === "bot" && !msg.sub && (
                  <img src={LA_IA_AVATAR} alt="La IA" className="w-6 h-6 rounded-full shrink-0" />
                )}
                <div
                  className={`max-w-[80%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                    msgStyles[msg.sub ? "sub" : msg.type === "emergency" ? "emergency" : msg.type === "error" ? "error" : msg.type === "success" ? "success" : msg.role] || msgStyles.bot
                  }`}
                >
                  {formatText(msg.text)}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-end gap-2">
                <img src={LA_IA_AVATAR} alt="La IA" className="w-6 h-6 rounded-full shrink-0" />
                <div className="bg-gray-100 text-gray-500 px-3 py-2 rounded-xl text-sm italic">
                  <span className="animate-pulse">Pensando...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* ─── Input ───────────────────────────────────── */}
          <div className="border-t p-3 flex items-center gap-2 bg-white shrink-0">
            {!disabled && (
              <button
                onClick={voiceMode ? toggleVoiceMode : () => { if (!disabledRef.current) { setVoiceMode(true); setWakeMode(true); startWakeListening(); } }}
                className={`p-2 rounded-lg transition ${listening ? "bg-red-500 text-white animate-pulse" : voiceMode ? "bg-green-100 text-green-600" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
                title={listening ? "Grabando..." : voiceMode ? "Modo voz activo" : "Presiona para hablar"}
              >
                {listening ? <MicOff size={18} /> : <Mic size={18} />}
              </button>
            )}
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={disabled ? "Desactivada. Escribe 'Eva Salud'..." : voiceMode ? "Usa tu voz o escribe..." : "Escribe tu consulta..."}
              className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={voiceMode && listening}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="bg-blue-700 text-white p-2 rounded-lg hover:bg-blue-800 disabled:opacity-50 transition"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}

      {/* ─── Botón flotante ──────────────────────────────── */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-4 right-4 z-50 bg-blue-900 text-white p-3.5 rounded-full shadow-lg hover:bg-blue-800 transition hover:scale-105 active:scale-95"
        title="Abrir La IA"
      >
        {open ? (
          <X size={24} />
        ) : (
          <img src={LA_IA_AVATAR} alt="La IA" className="w-7 h-7" />
        )}
      </button>
    </>
  );
}

export default LaIAChat;
