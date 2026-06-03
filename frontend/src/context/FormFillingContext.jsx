import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";

const FormFillingContext = createContext(null);
const STORAGE_KEY = "laia_form_filling_session_v2";
const RISK_KEY = "laia_risk_data_v2";

function loadStoredSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || parsed.completed || parsed.cancelled) return null;
    return parsed;
  } catch {
    return null;
  }
}

function persistSession(session) {
  try {
    if (!session || session.completed || session.cancelled) {
      localStorage.removeItem(STORAGE_KEY);
      return;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {
    // No bloquear el sistema si localStorage falla.
  }
}

function loadStoredRiskData() {
  try {
    const raw = localStorage.getItem(RISK_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function persistRiskData(data) {
  try {
    if (!data) localStorage.removeItem(RISK_KEY);
    else localStorage.setItem(RISK_KEY, JSON.stringify(data));
  } catch {
    // No bloquear el sistema si localStorage falla.
  }
}

export function FormFillingProvider({ children }) {
  const initialSession = loadStoredSession();
  const [session, setSession] = useState(initialSession);
  const sessionRef = useRef(initialSession);
  const [riskDataState, setRiskDataState] = useState(loadStoredRiskData());

  useEffect(() => {
    persistSession(session);
  }, [session]);

  const startFilling = useCallback((entity, fields, prefill = {}) => {
    const safeFields = Array.isArray(fields) ? fields : [];
    const firstMissingIndex = safeFields.findIndex((f) => !prefill?.[f.name]);
    const newSession = {
      entity,
      fields: safeFields,
      currentFieldIndex: firstMissingIndex >= 0 ? firstMissingIndex : 0,
      values: { ...(prefill || {}) },
      completed: false,
      cancelled: false,
      updatedAt: new Date().toISOString(),
    };
    sessionRef.current = newSession;
    setSession(newSession);
  }, []);

  const setCurrentValue = useCallback((name, value) => {
    setSession((prev) => {
      if (!prev) return prev;
      const fieldIdx = prev.fields.findIndex((f) => f.name === name);
      const newValues = { ...prev.values, [name]: value };
      const nextIndex = fieldIdx >= 0 ? fieldIdx + 1 : prev.currentFieldIndex;
      const newSession = {
        ...prev,
        values: newValues,
        currentFieldIndex: Math.max(nextIndex, prev.currentFieldIndex),
        updatedAt: new Date().toISOString(),
      };
      sessionRef.current = newSession;
      return newSession;
    });
  }, []);

  const resetField = useCallback((name) => {
    setSession((prev) => {
      if (!prev) return prev;
      const fieldIdx = prev.fields.findIndex((f) => f.name === name);
      if (fieldIdx < 0) return prev;
      const newValues = { ...prev.values };
      delete newValues[name];
      const newSession = {
        ...prev,
        values: newValues,
        currentFieldIndex: fieldIdx,
        completed: false,
        cancelled: false,
        updatedAt: new Date().toISOString(),
      };
      sessionRef.current = newSession;
      return newSession;
    });
  }, []);

  const nextField = useCallback(() => {
    setSession((prev) => {
      if (!prev) return prev;
      const nextIdx = prev.currentFieldIndex + 1;
      if (nextIdx >= prev.fields.length) {
        const completed = {
          ...prev,
          currentFieldIndex: prev.fields.length,
          completed: true,
          updatedAt: new Date().toISOString(),
        };
        sessionRef.current = completed;
        persistSession(null);
        return completed;
      }
      const next = { ...prev, currentFieldIndex: nextIdx, updatedAt: new Date().toISOString() };
      sessionRef.current = next;
      return next;
    });
  }, []);

  const setFieldIndex = useCallback((index) => {
    setSession((prev) => {
      if (!prev) return prev;
      const safeIndex = Math.max(0, Math.min(index, prev.fields.length));
      const newSession = {
        ...prev,
        currentFieldIndex: safeIndex,
        completed: false,
        cancelled: false,
        updatedAt: new Date().toISOString(),
      };
      sessionRef.current = newSession;
      return newSession;
    });
  }, []);

  const completeFilling = useCallback(() => {
    setSession((prev) => {
      if (!prev) return prev;
      const done = {
        ...prev,
        completed: true,
        currentFieldIndex: prev.fields.length,
        updatedAt: new Date().toISOString(),
      };
      sessionRef.current = done;
      persistSession(null);
      return done;
    });
  }, []);

  const cancelFilling = useCallback(() => {
    sessionRef.current = null;
    setSession(null);
    persistSession(null);
  }, []);

  const resumeFilling = useCallback(() => {
    const stored = loadStoredSession();
    if (!stored) return null;
    sessionRef.current = stored;
    setSession(stored);
    return stored;
  }, []);

  const setRiskData = useCallback((data) => {
    setRiskDataState(data);
    persistRiskData(data);
  }, []);

  const getSession = useCallback(() => sessionRef.current, []);

  return (
    <FormFillingContext.Provider
      value={{
        session,
        startFilling,
        setCurrentValue,
        nextField,
        resetField,
        setFieldIndex,
        completeFilling,
        cancelFilling,
        resumeFilling,
        getSession,
        riskData: riskDataState,
        setRiskData,
      }}
    >
      {children}
    </FormFillingContext.Provider>
  );
}

export function useFormFilling() {
  const ctx = useContext(FormFillingContext);
  if (!ctx) {
    throw new Error("useFormFilling debe usarse dentro de FormFillingProvider");
  }
  return ctx;
}
