import { useCallback } from "react";
import {
  extractEmailOnly,
  fieldIsDate,
  fieldIsDni,
  fieldIsEmail,
  fieldIsPhone,
  hasEmailLike,
  isValidEmail,
  normalizeEmail,
  normalizeFieldValue,
  normalizePersonName,
} from "../utils/normalizers";
import { buildFinalSummary } from "../utils/correctionEngine";
import { obtenerEsquemaFormulario, enviarFormularioIA } from "../services/laiaApi";

function isCommandOnlyDoctor(raw) {
  const t = String(raw || "").toLowerCase();
  return /(crear|registrar|agregar|nuevo|nueva)/.test(t) && /(médico|medico|doctor|doctora)/.test(t) && !hasEmailLike(t);
}

function isFieldName(field, names = []) {
  return names.includes(field?.name);
}

function fieldIsPersonName(field) {
  return isFieldName(field, ["nombres", "apellidos", "first_name", "last_name"]);
}

const FRASES_CONTROL = [
  "esta bien", "todo correcto", "solo cambia",
  "corrige", "corregir", "cambiar",
  "guardar", "cancelar",
];

function buildQuestionForField(entity, field) {
  const name = field?.name;
  const label = String(field?.label || field?.name || "campo").toLowerCase();

  if (entity === "doctor" || entity === "medico") {
    if (["nombres", "first_name"].includes(name)) return "¿Cuáles son los nombres del médico? Ejemplo: Luis Alberto.";
    if (["apellidos", "last_name"].includes(name)) return "¿Cuáles son los apellidos del médico? Ejemplo: Quispe Mamani.";
    if (["especialidad", "specialty"].includes(name)) return "¿Cuál es la especialidad del médico? Ejemplo: Cardiología.";
    if (["correo", "correo_electronico", "email"].includes(name)) return "¿Cuál es el correo electrónico real del médico? Ejemplo: luis.quispe@gmail.com.";
  }

  return `¿Cuál es ${label}?`;
}

function goToNextField({ fields, idx, values, completeFilling, awaitingFinalConfirmation, getSession, setResponse, setTranscript, speak, cmdFn }) {
  const nextIdx = idx + 1;

  if (nextIdx >= fields.length) {
    completeFilling();
    awaitingFinalConfirmation.current = true;

    const currentSession = getSession();
    const msg = buildFinalSummary(currentSession?.entity, currentSession?.values || values);

    setResponse(msg);
    setTranscript("");
    speak(msg, () => cmdFn.current?.());
    return;
  }

  const nextField = fields[nextIdx];
  const question = buildQuestionForField(getSession()?.entity, nextField);
  setResponse(question);
  setTranscript("");
  speak(question, () => cmdFn.current?.());
}

export function useLaIAFlow({
  session,
  startFilling,
  setCurrentValue,
  resetField,
  setFieldIndex,
  completeFilling,
  cancelFilling,
  getSession,
  setRiskData,
  setActivePage,
  onAction,
  setResponse,
  setTranscript,
  setState,
  speak,
  cmdFn,
  chainRef,
  processInputRef,
  awaitingFinalConfirmation,
  correctionMode,
  correctionField,
  log,
}) {
  const submitForm = useCallback(async () => {
    const s = getSession();
    if (!s) return;

    const vals = s.values;
    const entity = s.entity;

    log(`enviando ${entity}: ${JSON.stringify(vals).slice(0, 100)}`);
    setState("processing");

    try {
      const data = await enviarFormularioIA(entity, vals);

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
      if (chain && (entity === "patient" || entity === "doctor" || entity === "paciente" || entity === "medico") && chain.action === "agendar_cita") {
        chainRef.current = null;
        setTimeout(() => processInputRef.current?.(chain.text), 600);
        return;
      }

      chainRef.current = null;
      speak(data.voice || msg, () => cmdFn.current?.());
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 422 && Array.isArray(detail)) {
        const getLoc = (d) => {
          const loc = d.loc || [];
          return loc[loc.length - 1];
        };

        const badField = detail.map(getLoc).filter(Boolean)[0];
        log(`error validación en: ${badField || "desconocido"}`);

        const field = badField && s.fields ? s.fields.find((f) => f.name === badField) : null;
        const errMsg = detail.find((d) => getLoc(d) === badField)?.msg || "dato inválido";

        if (field && badField) {
          resetField(badField);
          const badIdx = s.fields.findIndex((f) => f.name === badField);
          if (badIdx >= 0) setFieldIndex(badIdx);
        }

        const label = field ? field.label.toLowerCase() : badField || "campo";
        const question = `El ${label} es incorrecto: ${errMsg}. Dímelo de nuevo para corregir solo ese campo.`;
        setResponse(question);
        setState("idle");
        speak(question, () => cmdFn.current?.());
        return;
      }

      const msg = err.response?.data?.detail || err.response?.data?.message || "Error de conexión.";
      setResponse(`Error: ${typeof msg === "string" ? msg : JSON.stringify(msg)}`);
      cancelFilling();
      speak("Error al guardar. Intenta de nuevo.", () => cmdFn.current?.());
    }
  }, [getSession, log, setState, setResponse, cancelFilling, speak, cmdFn, setActivePage, onAction, chainRef, processInputRef, resetField, setFieldIndex]);

  const handleFieldValue = useCallback(async (rawValue) => {
    if (!session || session.completed || session.cancelled) return false;

    const rawLower = String(rawValue || "").toLowerCase().trim().normalize("NFKD").replace(/[\u0300-\u036f]/g, "");
    if (FRASES_CONTROL.some((f) => rawLower.includes(f))) {
      return false;
    }

    const fields = session.fields || [];
    const idx = session.currentFieldIndex;
    if (idx >= fields.length) return false;

    const field = fields[idx];
    const value = normalizeFieldValue(field, rawValue);
    const entity = session.entity;
    const fieldName = field.name;

    // Reglas críticas para médico: nunca guardar correo como nombre/apellido.
    if ((entity === "doctor" || entity === "medico") && fieldIsPersonName(field) && hasEmailLike(rawValue)) {
      const question = ["nombres", "first_name"].includes(fieldName)
        ? "Ese dato parece un correo. Ahora necesito solo los nombres del médico."
        : "Ese dato parece un correo. Ahora necesito solo los apellidos del médico.";

      log(`dato rechazado para ${fieldName}: parece correo "${String(rawValue).slice(0, 40)}"`);
      setResponse(question);
      setTranscript("");
      setState("idle");
      speak(question, () => cmdFn.current?.());
      return true;
    }

    // Médico: campo por campo según schema.
    if ((entity === "doctor" || entity === "medico") && ["nombres", "first_name"].includes(fieldName)) {
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

      log(`rellenando ${fieldName}: "${nombres}"`);
      setCurrentValue(fieldName, nombres);

      const lastIdx = fields.findIndex((f) => ["apellidos", "last_name"].includes(f.name));
      if (lastIdx >= 0) {
        setFieldIndex(lastIdx);
        const question = "¿Cuáles son los apellidos del médico? Ejemplo: Quispe Mamani.";
        setResponse(question);
        setTranscript("");
        speak(question, () => cmdFn.current?.());
        return true;
      }
    }

    if ((entity === "doctor" || entity === "medico") && ["apellidos", "last_name"].includes(fieldName)) {
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

      log(`rellenando ${fieldName}: "${apellidos}"`);
      setCurrentValue(fieldName, apellidos);

      const specIdx = fields.findIndex((f) => ["especialidad", "specialty"].includes(f.name));
      if (specIdx >= 0) {
        setFieldIndex(specIdx);
        const question = "¿Cuál es la especialidad del médico? Ejemplo: Cardiología.";
        setResponse(question);
        setTranscript("");
        speak(question, () => cmdFn.current?.());
        return true;
      }
    }

    if (fieldIsEmail(field)) {
      const emailOnly = extractEmailOnly(rawValue);
      if (!emailOnly || !isValidEmail(emailOnly)) {
        const question = "Correo inválido. Dime el correo completo. Ejemplo: jhandeljesuschavezmiranda4 arroba gmail punto com.";
        log(`email inválido: "${rawValue}"`);
        setResponse(question);
        setTranscript("");
        setState("idle");
        speak(question, () => cmdFn.current?.());
        return true;
      }

      log(`rellenando ${fieldName}: "${emailOnly}"`);
      setCurrentValue(fieldName, emailOnly);
      goToNextField({ fields, idx, values: { ...session.values, [fieldName]: emailOnly }, completeFilling, awaitingFinalConfirmation, getSession, setResponse, setTranscript, speak, cmdFn });
      return true;
    }

    if (fieldIsDate(field) && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?$/.test(String(value))) {
      const question = "No entendí bien la fecha. Dímela así: día, mes y año. Ejemplo: 03 de junio de 2022.";
      log(`fecha inválida para ${fieldName}: "${value}"`);
      setResponse(question);
      setTranscript("");
      setState("idle");
      speak(question, () => cmdFn.current?.());
      return true;
    }

    if (fieldIsDni(field) && String(value).replace(/\D/g, "").length !== 8) {
      const question = "El DNI debe tener exactamente 8 dígitos. Repítelo número por número, por ejemplo: 1 2 3 4 5 6 7 8.";
      log(`dni inválido: "${value}"`);
      setResponse(question);
      setTranscript("");
      setState("idle");
      speak(question, () => cmdFn.current?.());
      return true;
    }

    if (fieldIsPhone(field) && String(value).replace(/\D/g, "").length !== 9) {
      const question = "El teléfono debe tener exactamente 9 dígitos. Repítelo nuevamente.";
      log(`teléfono inválido: "${value}"`);
      setResponse(question);
      setTranscript("");
      setState("idle");
      speak(question, () => cmdFn.current?.());
      return true;
    }

    log(`rellenando ${fieldName}: "${String(value).slice(0, 40)}" (raw: "${String(rawValue).slice(0, 30)}")`);
    setCurrentValue(fieldName, value);

    if (correctionMode?.current) {
      correctionMode.current = false;
      correctionField.current = null;
      completeFilling();
      awaitingFinalConfirmation.current = true;
      const currentSession = getSession();
      const msg = buildFinalSummary(currentSession?.entity, currentSession?.values || session.values);
      setResponse(msg);
      setTranscript("");
      speak(msg, () => cmdFn.current?.());
      return true;
    }

    goToNextField({ fields, idx, values: { ...session.values, [fieldName]: value }, completeFilling, awaitingFinalConfirmation, getSession, setResponse, setTranscript, speak, cmdFn });
    return true;
  }, [session, log, setResponse, setTranscript, setState, speak, cmdFn, setCurrentValue, setFieldIndex, completeFilling, correctionMode, correctionField, awaitingFinalConfirmation, getSession]);

  const startCreateFlow = useCallback(async (action, prefillData = {}) => {
    const entityMap = {
      crear_paciente: "patient",
      crear_medico: "doctor",
      agendar_cita: "appointment",
      crear_paciente_es: "paciente",
      crear_medico_es: "medico",
      agendar_cita_es: "cita",
    };

    const entity = entityMap[action] || action;
    if (!entity) return false;

    log(`iniciando flujo crear ${entity} con ${Object.keys(prefillData || {}).length} campos prellenados`);

    try {
      const schema = await obtenerEsquemaFormulario(entity);
      if (schema.error) {
        log(`schema error: ${schema.error}`);
        return false;
      }

      const fields = schema.fields || [];
      let safePrefill = { ...(prefillData || {}) };

      if (entity === "doctor" || entity === "medico") {
        for (const key of ["nombres", "first_name", "apellidos", "last_name"]) {
          if (safePrefill[key] && hasEmailLike(safePrefill[key])) delete safePrefill[key];
          if (safePrefill[key] && isCommandOnlyDoctor(safePrefill[key])) delete safePrefill[key];
        }

        for (const key of ["correo", "correo_electronico", "email"]) {
          if (safePrefill[key] && !isValidEmail(normalizeEmail(safePrefill[key]))) delete safePrefill[key];
        }
      }

      startFilling(entity, fields, safePrefill);

      const targetMap = {
        patient: "patients",
        paciente: "patients",
        doctor: "doctors",
        medico: "doctors",
        appointment: "appointments",
        cita: "appointments",
      };

      const tgt = targetMap[entity];
      if (tgt && setActivePage) setActivePage(tgt);
      if (onAction) onAction();

      const firstUnfilled = fields.find((f) => !safePrefill[f.name]);
      if (firstUnfilled) {
        const question = `Voy a guiarte paso a paso. ${buildQuestionForField(entity, firstUnfilled)}`;
        setResponse(question);
        setTranscript("");
        speak(question, () => cmdFn.current?.());
        return true;
      }

      completeFilling();
      awaitingFinalConfirmation.current = true;
      const currentSession = getSession();
      const msg = buildFinalSummary(currentSession?.entity || entity, currentSession?.values || safePrefill);
      setResponse(msg);
      setTranscript("");
      speak(msg, () => cmdFn.current?.());
      return true;
    } catch (e) {
      log(`error al obtener schema: ${e.message}`);
      return false;
    }
  }, [log, startFilling, setActivePage, onAction, setResponse, setTranscript, speak, cmdFn, completeFilling, awaitingFinalConfirmation, getSession]);

  return {
    handleFieldValue,
    submitForm,
    startCreateFlow,
  };
}
