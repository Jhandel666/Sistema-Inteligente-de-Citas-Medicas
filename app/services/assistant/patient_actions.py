from __future__ import annotations

import re
from app.core.exceptions import NotFoundException, ConflictException
from app.schemas.patient import PatientUpdate
from app.services.patient_service import PatientService
from app.services.assistant.intent_detector import extraer_datos_paciente
from app.services.assistant.name_utils import (
    aplicar_correccion_letra,
    buscar_por_nombre_fonetico,
    reconstruir_nombre_deletreado,
)


class PatientActions:
    def __init__(self, patient_service: PatientService) -> None:
        self.service = patient_service

    _STOP_WORDS = frozenset({
        "una", "unas", "uno", "unos", "un",
        "nuevo", "nueva", "nuevos", "nuevas",
        "paciente", "pacientes",
        "cita", "citas",
        "para", "por", "con", "sin", "del", "de", "en", "el", "la", "los", "las", "lo", "le",
        "traemos", "tiene", "tienen",
        "que", "es", "se", "su", "sus",
        "como", "este", "esta", "esto",
        "crear", "registrar", "agregar",
        "sobre", "entre", "hacia",
        "cuando", "donde",
        "usted", "tu", "mi",
    })


    @staticmethod
    def _prefill_paciente_es(datos: dict) -> dict:
        """Construye prefill usando los campos reales del schema PacienteCrear."""
        prefill = {
            "nombres": (datos.get("nombres") or datos.get("first_name") or "").title(),
            "apellidos": (datos.get("apellidos") or datos.get("last_name") or "").title(),
            "numero_documento": str(datos.get("numero_documento") or datos.get("document_number") or "").replace(" ", ""),
        }
        telefono = datos.get("telefono") or datos.get("phone")
        correo = datos.get("correo") or datos.get("email")
        fecha = datos.get("fecha_nacimiento") or datos.get("birth_date")
        genero = datos.get("genero") or datos.get("gender")
        if telefono:
            prefill["telefono"] = str(telefono).replace(" ", "")
        if correo:
            prefill["correo"] = str(correo).lower()
        if fecha:
            prefill["fecha_nacimiento"] = fecha
        if genero:
            prefill["genero"] = genero
        return prefill

    def _buscar(self, text: str, user_name: str = ""):
        pacientes = self.service.listar_pacientes(limite=100)
        text_lower = text.lower()

        nombre_extraido = None
        for pat in [
            r"(?:para|paciente)\s+(?:el\s+|la\s+|un\s+|una\s+)?(.+?)(?:\s+con\s+|\s+DNI\s+|\s+para\s+|\s+el\s+|\s+del?\s+(?:dr|doctor|médico|medico|especialista)|\s*$)",
            r"(?:crear|agendar|registrar)\s+cita\s+(?:médica|medica|para|con)\s+(?:el\s+|la\s+|un\s+|una\s+)?(.+?)(?:\s+con\s+|\s+para\s+|\s+del?\s+(?:dr|doctor|médico|medico|especialista)|\s*$)",
            r"soy\s+(.+)", r"me llamo\s+(.+)", r"mi nombre es\s+(.+)"            
        ]:
            m = re.search(pat, text_lower)
            if m:
                nombre_extraido = m.group(1).strip()
                break

        dni_match = re.search(r"\b(\d{8})\b", text)
        if dni_match:
            dni = dni_match.group(1)
            for p in pacientes:
                if p.document_number == dni:
                    return p

        if nombre_extraido:
            palabras_extra = nombre_extraido.split()
            for p in pacientes:
                nombre_completo = f"{p.first_name} {p.last_name}".lower()
                nombre_parts = nombre_completo.split()
                if sum(1 for w in palabras_extra if w in nombre_parts) >= 2:
                    return p

        palabras = [w for w in text_lower.split() if w not in self._STOP_WORDS]
        for p in pacientes:
            nombre_completo = f"{p.first_name} {p.last_name}".lower()
            nombre_parts = [w for w in nombre_completo.split() if w not in self._STOP_WORDS]
            if sum(1 for w in palabras if w in nombre_parts) >= 2:
                return p

        for p in pacientes:
            ln = p.last_name.lower()
            if ln not in self._STOP_WORDS and ln in text_lower:
                return p

        email_match = re.search(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b", text)
        if email_match:
            found = next((p for p in pacientes if p.email == email_match.group(0)), None)
            if found:
                return found

        # Solo usar user_name como fallback si el usuario habla de si mismo
        soy_match = re.search(r"\b(?:soy|me llamo|mi nombre es|para mi)\b", text_lower)
        if user_name and soy_match:
            user_parts = user_name.lower().split()
            for p in pacientes:
                nombre_completo = f"{p.first_name} {p.last_name}".lower()
                if all(part in nombre_completo for part in user_parts if len(part) > 2):
                    return p
            for p in pacientes:
                if p.first_name.lower() in user_name.lower() or p.last_name.lower() in user_name.lower():
                    return p

        # ── Fallback fonético: fuzzy match + deletreo + variantes de voz ──
        nombres_disponibles = [f"{p.first_name} {p.last_name}" for p in pacientes]

        # Generar candidatos de búsqueda: nombre extraído, palabra sueltas significativas,
        # nombre deletreado reconstruido, y texto con corrección "con X"
        candidatos = set()
        if nombre_extraido:
            # Filtrar stop words del nombre extraído antes de usarlo como candidato fonético
            extra_words = [w for w in nombre_extraido.split() if w not in self._STOP_WORDS]
            if extra_words:
                candidatos.add(" ".join(extra_words))
        # NOTA: Solo usamos nombre_extraido como candidato fonético, NO palabras aleatorias del texto,
        # para evitar falsos positivos (ej: "Rocio Miranda Ramos" coincide con paciente "Jhandel...Miranda")
        deletreado = reconstruir_nombre_deletreado(text)
        if deletreado:
            candidatos.add(deletreado)
            corregido = aplicar_correccion_letra(text, deletreado)
            if corregido and corregido != deletreado:
                candidatos.add(corregido)

        for c in sorted(candidatos, key=len, reverse=True):
            mejor = buscar_por_nombre_fonetico(c, nombres_disponibles)
            if mejor:
                idx = nombres_disponibles.index(mejor)
                return pacientes[idx]

        raise NotFoundException(
            "No se encontró el paciente. Proporciona DNI, nombre completo o email.\n"
            f"Pacientes disponibles: {', '.join(f'{p.first_name} {p.last_name}' for p in pacientes[:5])}"
        )

    def prefill_patient(self, text: str, entities: dict | None = None, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        datos = extraer_datos_paciente(text)
        if (not datos["first_name"] or not datos["document_number"]) and entities:
            pend = entities.get("_pending_patient", {})
            if pend.get("first_name") and pend.get("document_number"):
                for k in datos:
                    if not datos[k] and pend.get(k):
                        datos[k] = pend[k]

        missing = []
        if not datos["first_name"]:
            missing.append("nombre completo")
        if not datos["document_number"]:
            missing.append("número de DNI")

        if missing:
            return {
                "type": "info",
                "message": f"{nombre}, voy a guiarte paso a paso para crear el paciente.",
                "action": "crear_paciente",
                "target": "patients",
            }

        prefill = self._prefill_paciente_es(datos)

        campos_faltantes = []
        if not datos["phone"]:
            campos_faltantes.append("teléfono")
        if not datos["email"]:
            campos_faltantes.append("email")
        if not datos["birth_date"]:
            campos_faltantes.append("fecha de nacimiento")
        if not datos["gender"]:
            campos_faltantes.append("sexo (masculino/femenino)")

        msg = f"{nombre}, he preparado algunos datos. Te guiaré para completar el resto."

        return {
            "type": "prefill",
            "action": "crear_paciente",
            "target": "patients",
            "message": msg,
            "prefill": prefill,
        }

    def crear(self, text: str, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        datos = extraer_datos_paciente(text)

        missing = []
        if not datos["first_name"]:
            missing.append("nombre completo")
        if not datos["document_number"]:
            missing.append("número de DNI")

        if missing:
            return {
                "type": "info",
                "message": f"{nombre}, voy a guiarte paso a paso para crear el paciente.",
                "action": "crear_paciente",
                "target": "patients",
            }

        prefill = self._prefill_paciente_es(datos)

        return {
            "type": "prefill",
            "action": "crear_paciente",
            "target": "patients",
            "message": f"{nombre}, he preparado los datos del paciente. Te guiaré para completar el resto.",
            "prefill": prefill,
        }

    def eliminar(self, text: str, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        try:
            paciente = self._buscar(text, user_name=user_name)
            self.service.eliminar_paciente(paciente.id)
            return {
                "type": "success",
                "message": f"{nombre}, paciente {paciente.first_name} {paciente.last_name} eliminado exitosamente.",
                "action": "eliminar_paciente",
                "target": "patients",
            }
        except NotFoundException as e:
            return {
                "type": "info",
                "message": str(e),
                "action": "eliminar_paciente",
                "target": "patients",
            }
        except ConflictException as e:
            return {
                "type": "error",
                "message": str(e),
                "action": "eliminar_paciente",
                "target": "patients",
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error al eliminar paciente: {str(e)}",
                "action": "eliminar_paciente",
                "target": "patients",
            }

    def listar(self, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        return {
            "type": "success",
            "message": f"{nombre}, te he llevado a la sección de pacientes.\n¿Deseas **agregar**, **eliminar** o **actualizar** algún paciente?",
            "action": "ver_pacientes",
            "target": "patients",
        }
