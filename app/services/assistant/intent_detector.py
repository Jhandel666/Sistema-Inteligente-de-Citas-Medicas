from __future__ import annotations

import re
import unicodedata
from datetime import datetime


def _normalize(text: str) -> str:
    """Quita acentos y pasa a minusculas."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.lower()


_ESTADOS_CITA = {
    "pending": "Pendiente",
    "confirmed": "Confirmada",
    "cancelled": "Cancelada",
    "rescheduled": "Reprogramada",
    "PENDING": "Pendiente",
    "CONFIRMED": "Confirmada",
    "CANCELLED": "Cancelada",
    "RESCHEDULED": "Reprogramada",
}

def fmt_estado(status) -> str:
    if hasattr(status, "value"):
        return _ESTADOS_CITA.get(status.value, str(status.value))
    return _ESTADOS_CITA.get(str(status), str(status))


_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

_NUMEROS = {
    "cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14,
    "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
    "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25,
    "veintiseis": 26, "veintisiete": 27, "veintiocho": 28,
    "veintinueve": 29, "treinta": 30,
}

_INTENT_RULES: list[tuple[list[str], str]] = [
    (["agendar", "reservar", "sacar", "separar", "programar", "crear cita", "crear una cita", "crear cita medica", "crear cita médica", "dar cita", "dar una cita", "dar cita medica", "dar cita médica", "quiero una cita", "necesito una cita", "nueva cita"], "agendar_cita"),
    (["cancelar", "anular", "eliminar cita", "dar de baja"], "cancelar_cita"),
    (["estado", "consultar", "ver mi cita", "saber mi cita", "confirmada", "pendiente", "citas", "mis citas", "lista citas", "dictame", "recientes", "mostrar citas", "ver citas", "citas medicas"], "consultar_cita"),
    (["reprogramar", "cambiar fecha", "cambiar hora", "mover cita", "adelantar", "postergar", "modificar cita"], "reprogramar_cita"),
    (["que medico", "que doctor", "medicos disponibles", "doctores disponibles", "quien atiende", "especialista de", "atiende en", "atienden", "medicos atienden", "consulta externa"], "consultar_doctor"),
    (["llevame", "llevame a", "navegar", "ir a", "muestrame", "abrir", "menu de", "pantalla de", "dirigeme", "redirigeme", "ponme en"], "navegar"),
    (["emergencia", "urgencia", "accidente", "grave", "sangrando", "infarto", "dolor fuerte", "se cayo", "no respira", "desmayo", "convulsiones"], "emergencia"),
    (["horario", "informacion", "direccion", "costo", "precio", "seguro", "seguro sis", "seguro essalud", "essalud", "documentos", "requisitos", "info"], "informacion_servicios"),
    (["resultados", "laboratorio", "examen", "examenes", "analisis", "lab", "resultado de laboratorio"], "resultados_lab"),
    (["crear medico", "nuevo medico", "agregar medico", "registrar medico", "añadir medico", "dar de alta medico",
      "crear un nuevo medico", "agregar un nuevo medico", "registrar un nuevo medico"], "crear_medico"),
    (["crear paciente", "nuevo paciente", "agregar paciente", "registrar paciente", "añadir paciente",
      "crear un nuevo paciente", "agregar un nuevo paciente"], "crear_paciente"),
    (["eliminar medico", "borrar medico", "quitar medico", "dar de baja medico"], "eliminar_medico"),
    (["eliminar paciente", "borrar paciente", "quitar paciente", "dar de baja paciente"], "eliminar_paciente"),
    (["eliminar cita", "borrar cita", "quitar cita"], "eliminar_cita"),
    (["actualizar medico", "editar medico", "modificar medico", "cambiar medico"], "actualizar_medico"),
    (["actualizar paciente", "editar paciente", "modificar paciente", "cambiar paciente"], "actualizar_paciente"),
    (["ver pacientes", "mostrar pacientes", "lista pacientes", "todos los pacientes", "listado pacientes", "ver paciente",
      "quiero ver pacientes", "para ver pacientes"], "ver_pacientes"),
    (["ver medicos", "mostrar medicos", "lista medicos", "todos los medicos", "listado medicos",
      "quiero ver medicos", "para ver medicos"], "ver_medicos"),
    (["ver citas", "mostrar citas", "todas las citas", "listado citas", "lista citas", "ver todas las citas",
      "quiero ver citas", "para ver citas"], "ver_citas"),
    (["queja", "reclamo", "queja o reclamo", "libro de reclamaciones"], "queja_reclamo"),
    (["predecir riesgo", "riesgo de inasistencia", "riesgo inasistencia",
      "probabilidad de inasistencia", "predecir riesgo con ia", "predecir riesgo ia",
      "riesgo ia", "riesgo de ausencia", "probabilidad de ausencia",
      "nivel de riesgo", "predecir riesgo de inasistencia",
      "analizar riesgo", "evaluar riesgo", "calcular riesgo"], "predecir_riesgo"),
    (["confirmar cita", "confirmar la cita", "generar ticket", "crear ticket",
      "si confirmar", "si confirma", "confirmar", "ticket por favor",
      "generar el ticket", "sacar ticket", "dale confirmar"], "confirmar_cita"),
]

# ── Pares de palabras clave sueltas (si aparecen AMBAS, el intent es seguro) ──
_INTENT_WORD_PAIRS: list[tuple[list[list[str]], str]] = [
    ([["agregar", "medico"], ["crear", "medico"], ["nuevo", "medico"], ["registrar", "medico"],
      ["agregar", "doctor"], ["crear", "doctor"], ["nuevo", "doctor"]], "crear_medico"),
    ([["agregar", "paciente"], ["crear", "paciente"], ["nuevo", "paciente"], ["registrar", "paciente"]], "crear_paciente"),
    ([["eliminar", "medico"], ["borrar", "medico"], ["quitar", "medico"]], "eliminar_medico"),
    ([["eliminar", "paciente"], ["borrar", "paciente"], ["quitar", "paciente"]], "eliminar_paciente"),
    ([["ver", "paciente"], ["ver", "pacientes"], ["mostrar", "paciente"], ["mostrar", "pacientes"],
      ["listar", "paciente"], ["listar", "pacientes"]], "ver_pacientes"),
    ([["ver", "medico"], ["ver", "medicos"], ["mostrar", "medico"], ["mostrar", "medicos"],
      ["listar", "medico"], ["listar", "medicos"]], "ver_medicos"),
    ([["ver", "cita"], ["ver", "citas"], ["mostrar", "cita"], ["mostrar", "citas"],
      ["listar", "cita"], ["listar", "citas"]], "ver_citas"),
    ([["agendar", "cita"], ["reservar", "cita"], ["programar", "cita"], ["sacar", "cita"],
      ["nueva", "cita"], ["crear", "cita"], ["dar", "cita"], ["separar", "cita"]], "agendar_cita"),
    ([["cancelar", "cita"], ["anular", "cita"]], "cancelar_cita"),
    ([["consultar", "cita"], ["estado", "cita"]], "consultar_cita"),
    ([["reprogramar", "cita"], ["cambiar", "fecha", "cita"], ["cambiar", "hora", "cita"]], "reprogramar_cita"),
    ([["predecir", "riesgo"], ["riesgo", "inasistencia"], ["riesgo", "ausencia"],
      ["prediccion", "riesgo"], ["analizar", "riesgo"], ["evaluar", "riesgo"],
      ["calcular", "riesgo"], ["probabilidad", "inasistencia"]], "predecir_riesgo"),
    ([["confirmar", "cita"], ["generar", "ticket"], ["crear", "ticket"],
      ["sacar", "ticket"], ["ticket", "cita"]], "confirmar_cita"),
]


def detect_intent_by_rules(text: str) -> str | None:
    norm = _normalize(text)
    # 1. Frases exactas normalizadas
    for keywords, intent in _INTENT_RULES:
        for kw in keywords:
            if kw in norm:
                return intent
    # 2. Pares de palabras sueltas (ambas deben aparecer)
    words = set(norm.split())
    for pairs, intent in _INTENT_WORD_PAIRS:
        for pair in pairs:
            if all(w in words for w in pair):
                return intent
    return None


_ESPECIALIDADES_SINONIMOS: dict[str, list[str]] = {
    "medicina general": ["medicina", "general", "medico general", "medico", "médico"],
    "pediatria": ["pediatra", "niño", "niña", "bebe", "bebé", "pediatria"],
    "ginecologia": ["ginecologo", "ginecologa", "ginecologia", "ginecología", "matrona"],
    "cardiologia": ["cardiologo", "cardiologa", "corazon", "corazón", "cardiologia"],
    "traumatologia": ["traumatologo", "traumatologa", "traumatologia", "ortopedia", "huesos"],
    "oftalmologia": ["oftalmologo", "oftalmologa", "oftalmologia", "ojo", "ojos", "vista"],
    "dermatologia": ["dermatologo", "dermatologa", "dermatologia", "piel", "alergia", "alergias"],
    "psicologia": ["psicologo", "psicologa", "psicologia", "psicólogo", "ansiedad", "depresion", "depresión"],
    "nutricion": ["nutricionista", "nutricion", "dieta", "peso", "nutricional"],
    "odontologia": ["odontologo", "odontologa", "odontologia", "dentista", "diente", "muela", "dolor de muela"],
    "urologia": ["urologo", "urologia", "prostata", "próstata", "urinario"],
    "neurologia": ["neurologo", "neurologia", "cerebro", "cabeza", "migraña"],
    "medicina interna": ["medicina interna", "internista"],
    "neumologia": ["neumologo", "neumologa", "neumologia", "pulmon", "pulmón", "respiratorio"],
    "otorrinolaringologia": ["otorrino", "oido", "oído", "garganta", "nariz", "otorgino"],
    "cirugia general": ["cirujano", "cirugia", "cirugía", "operacion"],
}

_TURNOS = {
    "manana": ["mañana", "manana", "temprano", "8", "9", "10", "11", "12"],
    "tarde": ["tarde", "13", "14", "15", "16", "17", "18"],
}


def extract_entities(text: str) -> dict:
    entities: dict = {
        "patient": None,
        "patient_id": None,
        "doctor": None,
        "doctor_id": None,
        "specialty": None,
        "date": None,
        "time": None,
        "reason": None,
        "distance_km": None,
    }

    for especialidad, keywords in _ESPECIALIDADES_SINONIMOS.items():
        for kw in keywords:
            if kw in text:
                entities["specialty"] = especialidad
                break
        if entities["specialty"]:
            break

    date_patterns = [
        r"(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?",
        r"(\d{1,2})\s+de\s+([a-z]+)(?:\s+del?\s*(\d{2,4}))?",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 3 and groups[2]:
                if groups[1].isalpha():
                    entities["date"] = f"{groups[2]}-{_mes_num(groups[1]):02d}-{int(groups[0]):02d}"
                else:
                    entities["date"] = f"{groups[2]}-{int(groups[1]):02d}-{int(groups[0]):02d}"
            elif groups[1].isalpha():
                entities["date"] = f"{datetime.now().year}-{_mes_num(groups[1]):02d}-{int(groups[0]):02d}"
            else:
                entities["date"] = f"{datetime.now().year}-{int(groups[1]):02d}-{int(groups[0]):02d}"

    if not entities["date"]:
        if any(w in text for w in ["hoy", "ahora", "urgente"]):
            entities["date"] = datetime.now().strftime("%Y-%m-%d")
        elif any(w in text for w in ["mañana", "manana"]):
            from datetime import timedelta
            tomorrow = datetime.now() + timedelta(days=1)
            entities["date"] = tomorrow.strftime("%Y-%m-%d")
        elif any(w in text for w in ["pasado mañana", "pasado manana"]):
            from datetime import timedelta
            day_after = datetime.now() + timedelta(days=2)
            entities["date"] = day_after.strftime("%Y-%m-%d")
        elif any(w in text for w in ["semana que viene", "proxima semana", "próxima semana"]):
            from datetime import timedelta
            next_week = datetime.now() + timedelta(days=7)
            entities["date"] = next_week.strftime("%Y-%m-%d")

    # ─── Extraer hora ──────────────────────────────────────
    time_patterns = [
        r"(\d{1,2}):(\d{2})\s*(?:horas?|hrs?|h|am|pm)?",
        r"a\s+las\s+(\d{1,2})(?:\s*[.:]\s*(\d{2}))?\s*(?:de\s+la\s+)?(mañana|tarde|noche|madrugada)?",
        r"(\d{1,2})\s*(?:am|pm)",
        r"(?:a\s+las\s+)?(\d{1,2})\s*(?:horas?|hrs?|h)\s*(?:con\s+(\d{2}))?",
    ]
    for pattern in time_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            groups = m.groups()
            hour = int(groups[0])
            minute = int(groups[1]) if groups[1] else 0
            # Ajuste por periodo (mañana/tarde/noche)
            periodo = (groups[2] or "").lower() if len(groups) > 2 else ""
            if periodo in ("tarde", "noche") and hour < 12:
                hour += 12
            elif periodo == "madrugada" and hour >= 12:
                hour -= 12
            # am/pm explícito
            raw_match = m.group(0).lower()
            if "pm" in raw_match and hour < 12:
                hour += 12
            if "am" in raw_match and hour >= 12:
                hour -= 12
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                entities["time"] = f"{hour:02d}:{minute:02d}"
                break

    # ─── Extraer motivo ────────────────────────────────────
    motivo_keywords = ["por", "motivo", "razón", "razon", "porque", "por qué", "debido a"]
    motivo_stops = r"(?:cita|consulta|control|revisión|revision|dolor|molestia|fiebre|tos|gripe|dolor\s+de|con\s+el|con|del|de\s+la|para)"
    for kw in motivo_keywords:
        pattern = re.compile(
            rf"\b{re.escape(kw)}\b\s+(.+?)(?=\s*(?:{motivo_stops}|\s*y\s+|\s*,\s*$|\s*$))",
            re.IGNORECASE,
        )
        m = pattern.search(text)
        if m:
            extracted = m.group(1).strip().rstrip(".,;")
            if len(extracted) > 3:
                entities["reason"] = extracted
                break

    # ─── Extraer distancia (km) ────────────────────────────
    km_m = re.search(
        r"(?:a\s+)?(\d+(?:\.\d+)?)\s*(?:km|kilometros|kilómetros|kms)",
        text, re.IGNORECASE
    )
    if km_m:
        entities["distance_km"] = float(km_m.group(1))

    return entities


def _mes_num(nombre: str) -> int:
    return _MESES.get(nombre.lower(), 1)


_NAV_PAGES: dict[str, str] = {
    "dashboard": "dashboard",
    "inicio": "dashboard",
    "principal": "dashboard",
    "medicos": "doctors",
    "doctores": "doctors",
    "medico": "doctors",
    "pacientes": "patients",
    "paciente": "patients",
    "citas": "appointments",
    "cita": "appointments",
    "tickets": "appointments",
    "ia": "ai",
    "voz": "ai",
    "asistente": "ai",
    "inteligencia artificial": "ai",
}


def detectar_navegacion(text: str) -> str | None:
    """Detecta navegación solo con órdenes explícitas.

    Evita falsos positivos como ``melquiades`` -> ``ia``.
    """
    clean = _normalize(text)
    if not re.search(r"\b(llevame|llévame|abrir|abre|ir a|navegar|muestrame|muéstrame|menu|menú|pantalla|seccion|sección)\b", clean):
        return None

    for nombre, page in _NAV_PAGES.items():
        if re.search(rf"\b{re.escape(nombre)}\b", clean):
            return page
    return None


_PAGE_NAMES = {
    "dashboard": "Dashboard",
    "doctors": "Médicos",
    "patients": "Pacientes",
    "appointments": "Citas",
    "ai": "IA / Voz",
}


def nombre_pagina(target: str) -> str:
    return _PAGE_NAMES.get(target, target)


def limpiar_nombre(raw: str, strip_specialties: bool = False) -> tuple[str, str]:
    raw = re.sub(r"\b(?:doctor|docta|dra|dr|lic|ing)\.?\s*", "", raw, flags=re.IGNORECASE)
    if strip_specialties:
        all_kw = {kw for kws in _ESPECIALIDADES_SINONIMOS.values() for kw in kws}
        raw = re.sub(
            r"\b(?:" + "|".join(re.escape(kw) for kw in sorted(all_kw, key=len, reverse=True)) + r")\b",
            "", raw, flags=re.IGNORECASE
        )
    raw = raw.strip().title()
    parts = raw.split()
    if not parts:
        return ("", "")
    return (parts[0], " ".join(parts[1:]) if len(parts) > 1 else "")


def extraer_datos_paciente(text: str) -> dict:
    datos: dict = {"first_name": "", "last_name": "", "document_number": "", "phone": "", "email": "", "birth_date": "", "gender": ""}
    clean = re.sub(r"\b(doctor|docta|dra|dr|lic|ing)\.", r"\1", text, flags=re.IGNORECASE)

    # DNI: buscar 8 dígitos, posiblemente con espacios (ej: "60 00 5739")
    dni_m = re.search(r"(?<!\d)(\d)(?:\s*)(\d)(?:\s*)(\d)(?:\s*)(\d)(?:\s*)(\d)(?:\s*)(\d)(?:\s*)(\d)(?:\s*)(\d)(?!\d)", text)
    if dni_m:
        datos["document_number"] = "".join(dni_m.group(i) for i in range(1, 9))

    phone_m = re.search(r"(?<!\d)(9\d{8})(?!\d)", text)
    if phone_m:
        datos["phone"] = phone_m.group(1)
    else:
        # Phone with spaces: "987 132 831"
        phone_spaced = re.search(r"(?<!\d)(9)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)\s*(\d)(?!\d)", text)
        if phone_spaced:
            datos["phone"] = "".join(phone_spaced.group(i) for i in range(1, 10))

    # Normalizar dictado hablado a símbolos de email antes de buscar
    clean_email = clean.lower()
    # Limpiar prefijos comunes: "correo:", "mi correo es", "email:", etc.
    clean_email = re.sub(
        r"^(?:(?:mi|el|la|del?)\s+)?"
        r"(?:correo|email|correo\s+electronico|correo\s+electrónico)"
        r"(?:\s+(?:del?|del|del|del)\s+(?:paciente)?)?"
        r"\s*(?::\s*)?(?:es\s+)?"
        r"|\bpaciente\s*(?::\s*)?",
        "", clean_email)
    clean_email = re.sub(r"\barroba\b", "@", clean_email)
    clean_email = re.sub(r"\broba\b", "@", clean_email)
    clean_email = re.sub(r"\barrobe\b", "@", clean_email)
    clean_email = re.sub(r"\barova\b", "@", clean_email)
    clean_email = re.sub(r"\barroa\b", "@", clean_email)
    clean_email = re.sub(r"\bat\b", "@", clean_email)
    clean_email = re.sub(r"\bguion\s+bajo\b", "_", clean_email)
    clean_email = re.sub(r"\bguión\s+bajo\b", "_", clean_email)
    clean_email = re.sub(r"\bguion\b", "-", clean_email)
    clean_email = re.sub(r"\bguión\b", "-", clean_email)
    clean_email = re.sub(r"\bpunto\b", ".", clean_email)
    clean_email = re.sub(r"\bdot\b", ".", clean_email)
    clean_email = re.sub(r"\s*@\s*", "@", clean_email)
    clean_email = re.sub(r"\s*\.\s*", ".", clean_email)
    clean_email = re.sub(r"\.\s*com\b", ".com", clean_email)
    clean_email = re.sub(r"\.\s*pe\b", ".pe", clean_email)
    clean_email = re.sub(r"\.\s*es\b", ".es", clean_email)
    clean_email = re.sub(r"\.\s*org\b", ".org", clean_email)
    clean_email = re.sub(r"\.\s*net\b", ".net", clean_email)
    clean_email = re.sub(r"\.\s*gob\b", ".gob", clean_email)
    clean_email = re.sub(r"\.\s*edu\b", ".edu", clean_email)
    clean_email = re.sub(r"\s+", "", clean_email)
    # Eliminar acentos antes de buscar el email (á→a, é→e, etc.)
    clean_email = (clean_email
                   .replace("á", "a").replace("é", "e").replace("í", "i")
                   .replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ñ", "n"))
    email_m = re.search(r"\b([a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,})\b", clean_email)
    if email_m:
        datos["email"] = email_m.group(1)

    # Parsear fecha de nacimiento: "6 de noviembre del 2006", "6/11/2006", "6:11 del 2006", "6-11-2006"
    fecha_patrones = [
        r"(\d{1,2})\s*(?:de\s+)?([a-z]+)\s*(?:del?\s*)?(\d{4})",
        r"(\d{1,2})[/:\-](\d{1,2})[/:\-](\d{4})",
    ]
    for pat in fecha_patrones:
        fm = re.search(pat, text, re.IGNORECASE)
        if fm:
            g1, g2, g3 = fm.groups()
            if g2.isalpha():
                mes = _MESES.get(g2.lower(), 0)
                if mes:
                    datos["birth_date"] = f"{g3}-{mes:02d}-{int(g1):02d}"
            elif g2.isdigit():
                dia, mes = int(g1), int(g2)
                if mes > 12:
                    dia, mes = mes, dia
                datos["birth_date"] = f"{g3}-{mes:02d}-{dia:02d}"
            break

    # Género
    genero_lower = clean.lower()
    if re.search(r"\b(?:masculino|varon|hombre|masculino)\b", genero_lower):
        datos["gender"] = "masculino"
    elif re.search(r"\b(?:femenino|mujer|femenina)\b", genero_lower):
        datos["gender"] = "femenino"

    stops = r"\b(?:con|dni|telefono|email|correo|edad|fecha|nacimiento|apellido|apellidos|y|para|de|del|un|una|crear|crea|nuevo|nueva|cita|quiero)\b"

    for kw in ["nombre", "paciente", "llamado", "llamada", "registrar", "agregar", "añadir"]:
        pattern = re.compile(
            rf"\b{re.escape(kw)}\b\s+(?:paciente\s+|el\s+|la\s+|un\s+|una\s+)?"
            rf"([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*?)"
            rf"(?=\s*(?:{stops}|$))",
            re.IGNORECASE,
        )
        m = pattern.search(clean)
        if m:
            datos["first_name"], datos["last_name"] = limpiar_nombre(m.group(1))
            break

    # Fallback: si hay DNI pero no se extrajo nombre (o se extrajo una stop word), tomar palabras antes del DNI
    _STOP_NAMES = {"del", "para", "el", "la", "los", "las", "un", "una", "nombre", "paciente", "nuevo", "nueva", "crear", "llamado", "llamada", "apellido", "apellidos"}
    if (not datos["first_name"] or datos["first_name"].lower() in _STOP_NAMES) and datos["document_number"]:
        dni_pos = re.search(r"\b\d{8}\b", clean)
        if dni_pos:
            before = clean[:dni_pos.start()].strip()
            before = re.sub(r"\b(?:con|dni|telefono|email|correo|y|para|de|del|el|la|los|las|un|una|nombre|paciente|nuevo|nueva|crear|llamado|llamada)\b", "", before, flags=re.IGNORECASE).strip()
            words = before.split()
            if len(words) >= 2:
                datos["first_name"] = words[0]
                datos["last_name"] = " ".join(words[1:])

    return datos


def extraer_datos_medico(text: str) -> dict:
    datos: dict = {"first_name": "", "last_name": "", "specialty": "", "email": ""}
    clean = re.sub(r"\b(?:doctor|docta|dra|dr|lic|ing)\.", lambda m: m.group(0).replace(".", ""), text, flags=re.IGNORECASE)

    clean_email = clean.lower()
    clean_email = re.sub(r"\barroba\b", "@", clean_email)
    clean_email = re.sub(r"\broba\b", "@", clean_email)
    clean_email = re.sub(r"\barrobe\b", "@", clean_email)
    clean_email = re.sub(r"\barova\b", "@", clean_email)
    clean_email = re.sub(r"\barroa\b", "@", clean_email)
    clean_email = re.sub(r"\bat\b", "@", clean_email)
    clean_email = re.sub(r"\bguion\b", "-", clean_email)
    clean_email = re.sub(r"\bguión\b", "-", clean_email)
    clean_email = re.sub(r"\bpunto\b", ".", clean_email)
    clean_email = re.sub(r"\bdot\b", ".", clean_email)
    clean_email = re.sub(r"\s*@\s*", "@", clean_email)
    clean_email = re.sub(r"\s*\.\s*", ".", clean_email)
    clean_email = re.sub(r"\.\s*com\b", ".com", clean_email)
    clean_email = re.sub(r"\.\s*pe\b", ".pe", clean_email)
    clean_email = re.sub(r"\.\s*es\b", ".es", clean_email)
    clean_email = re.sub(r"\.\s*org\b", ".org", clean_email)
    clean_email = re.sub(r"\.\s*net\b", ".net", clean_email)
    clean_email = re.sub(r"\.\s*gob\b", ".gob", clean_email)
    clean_email = re.sub(r"\.\s*edu\b", ".edu", clean_email)
    clean_email = re.sub(r"\s+", "", clean_email)
    email_m = re.search(r"\b([a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,})\b", clean_email)
    if email_m:
        datos["email"] = email_m.group(1)

    text_lower = text.lower()
    for especialidad, keywords in _ESPECIALIDADES_SINONIMOS.items():
        for kw in keywords:
            if kw in text_lower:
                datos["specialty"] = especialidad
                break
        if datos["specialty"]:
            break

    stops = r"\b(?:con|especialidad|especialista|email|correo|en|de|para|y)\b"

    for kw in ["medico", "médico", "doctor", "dra", "dr", "crear", "registrar", "agregar", "añadir", "nuevo", "nueva", "llamado", "llamada", "nombre"]:
        pattern = re.compile(
            rf"\b{re.escape(kw)}\b\s+(?:medico\s+|médico\s+|el\s+|la\s+|un\s+|una\s+)?"
            rf"([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*?)"
            rf"(?=\s*(?:{stops}|$))",
            re.IGNORECASE,
        )
        m = pattern.search(clean)
        if m:
            datos["first_name"], datos["last_name"] = limpiar_nombre(m.group(1), strip_specialties=True)
            break

    return datos
