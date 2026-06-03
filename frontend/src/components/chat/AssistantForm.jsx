import { useState } from "react";
import api from "../../services/api";

function AssistantForm({ form, onSuccess, onError, speak }) {
  const [values, setValues] = useState(() => ({ ...(form.values || {}) }));
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fields = form.fields || [];
  const validationTemplates = {
    text: (v) => (!v || v.trim().length < 2 ? "Debe tener al menos 2 caracteres" : null),
    email: (v) => (!v ? null : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? "Correo inválido" : null),
    tel: (v) => {
      if (!v) return null;
      const digits = v.replace(/\D/g, "");
      if (!/^\d{9,}$/.test(digits)) return "Debe tener al menos 9 dígitos";
      if (!digits.startsWith("9")) return "Debe empezar con 9";
      return null;
    },
    date: (v) => {
      if (!v) return null;
      if (isNaN(Date.parse(v))) return "Fecha inválida";
      if (v.length >= 10 && new Date(v) < new Date(new Date().toDateString())) return "No puede ser una fecha pasada";
      return null;
    },
  };
  const patternValidators = {
    "\\d{8}": (v) => (!v ? null : !/^\d{8}$/.test(v) ? "Debe tener 8 dígitos" : null),
    "\\d{9}": (v) => {
      if (!v) return null;
      if (!/^\d{9}$/.test(v)) return "Debe tener 9 dígitos";
      if (!v.startsWith("9")) return "Debe empezar con 9";
      return null;
    },
  };

  function validateField(field, value) {
    if (field.required && (!value || !value.toString().trim())) return "Este campo es obligatorio";
    if (value && value.toString().trim()) {
      const template = validationTemplates[field.type];
      if (template) {
        const err = template(value.toString().trim());
        if (err) return err;
      }
      if (field.pattern) {
        const patternValidator = patternValidators[field.pattern];
        if (patternValidator) {
          const err = patternValidator(value.toString().trim());
          if (err) return err;
        }
      }
    }
    return null;
  }

  function validateAll() {
    const newErrors = {};
    fields.forEach((f) => {
      const err = validateField(f, values[f.name]);
      if (err) newErrors[f.name] = err;
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validateAll()) return;
    setSaving(true);
    try {
      const res = await api.post("/assistant/form-submit", {
        form_id: form.form_id,
        data: values,
      });
      const data = res.data;
      if (data.type === "success") {
        setValues({});
        setErrors({});
        onSuccess(data);
        if (speak && data.voice) speak(data.voice);
      } else {
        onError(data);
        if (speak && data.voice) speak(data.voice);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Error de conexión";
      onError({ type: "error", message: msg });
    }
    setSaving(false);
  }

  function handleChange(name, value) {
    if (value && value.toString().startsWith(" ") && !values[name]) return;
    setValues((prev) => ({ ...prev, [name]: value }));
    const field = fields.find((f) => f.name === name);
    if (field) {
      const err = validateField(field, value);
      setErrors((prev) => ({ ...prev, [name]: err }));
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 mt-2">
      {fields.map((field) => (
        <div key={field.name}>
          <label htmlFor={`assistant-${field.name}`} className="block text-xs font-medium text-gray-700 mb-0.5">
            {field.label}
            {field.required && <span className="text-red-500 ml-0.5">*</span>}
          </label>
          <input
            id={`assistant-${field.name}`}
            name={field.name}
            autoComplete={field.type === "email" ? "email" : field.type === "tel" ? "tel" : field.name.includes("name") ? "name" : "off"}
            type={field.type}
            value={values[field.name] || ""}
            onChange={(e) => handleChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            maxLength={field.max_length}
            className={`w-full border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 transition ${
              errors[field.name]
                ? "border-red-400 focus:ring-red-300 bg-red-50"
                : values[field.name]
                  ? "border-green-300 focus:ring-green-300"
                  : "border-gray-300 focus:ring-blue-400"
            }`}
            disabled={saving}
          />
          {errors[field.name] && (
            <p className="text-red-500 text-[10px] mt-0.5">{errors[field.name]}</p>
          )}
        </div>
      ))}
      <button
        type="submit"
        disabled={saving}
        className="w-full bg-blue-700 hover:bg-blue-800 disabled:bg-blue-400 text-white font-medium py-2 rounded-lg text-sm transition flex items-center justify-center gap-2"
      >
        {saving ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Guardando...
          </>
        ) : (
          form.submit_label || "Guardar"
        )}
      </button>
    </form>
  );
}

export default AssistantForm;
