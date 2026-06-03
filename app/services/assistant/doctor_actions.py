from __future__ import annotations

import re

from app.core.exceptions import NotFoundException
from app.services.doctor_service import DoctorService
from app.services.assistant.intent_detector import extraer_datos_medico
from app.services.assistant.name_utils import (
    aplicar_correccion_letra,
    buscar_por_nombre_fonetico,
    reconstruir_nombre_deletreado,
)


class DoctorActions:
    def __init__(self, doctor_service: DoctorService) -> None:
        self.service = doctor_service

    @staticmethod
    def _norm(txt: str) -> str:
        import unicodedata
        txt = unicodedata.normalize("NFKD", txt or "").encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", txt.lower()).strip()

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
    def _prefill_medico_es(datos: dict) -> dict:
        """Construye prefill usando los campos reales del schema MedicoCrear."""
        prefill: dict = {}
        nombres = datos.get("nombres") or datos.get("first_name")
        apellidos = datos.get("apellidos") or datos.get("last_name")
        especialidad = datos.get("especialidad") or datos.get("specialty")
        correo = datos.get("correo") or datos.get("email")
        if nombres:
            prefill["nombres"] = str(nombres).title()
        if apellidos:
            prefill["apellidos"] = str(apellidos).title()
        if especialidad:
            prefill["especialidad"] = str(especialidad).title()
        if correo:
            prefill["correo"] = str(correo).lower()
        return prefill

    def _buscar(self, text: str, specialty: str | None = None):
        doctores = self.service.listar_medicos()
        text_norm = self._norm(text)

        if not doctores:
            raise NotFoundException("No hay médicos registrados en el sistema.")

        # 1) Si el usuario dio nombre explícito del médico, buscar por nombre primero.
        #    No debe retornar el primer médico de la especialidad si el nombre no coincide.
        explicit_patterns = [
            r"(?:con\s+el\s+|con\s+la\s+)?(?:dr|doctor|doctora|dra|médico|medico)\s*\.?\s*([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+){0,4})",
            r"(?:medico|médico|doctor|doctora)\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+){0,4})",
        ]
        nombre_busqueda = ""
        for pat in explicit_patterns:
            m = re.search(pat, text_norm, re.IGNORECASE)
            if m:
                nombre_busqueda = m.group(1).strip()
                break

        if nombre_busqueda:
            # Quitar palabras de especialidad del nombre capturado.
            try:
                from app.services.assistant.intent_detector import _ESPECIALIDADES_SINONIMOS
                all_kw = {self._norm(kw) for kws in _ESPECIALIDADES_SINONIMOS.values() for kw in kws}
                words = [w for w in nombre_busqueda.split() if w not in all_kw and w not in self._STOP_WORDS]
            except Exception:
                words = [w for w in nombre_busqueda.split() if w not in self._STOP_WORDS]

            if words:
                for d in doctores:
                    doc_words = set(self._norm(f"{d.first_name} {d.last_name}").split())
                    if len(words) >= 2 and all(w in doc_words for w in words[:2]):
                        return d
                    if len(words) == 1 and words[0] in doc_words:
                        return d

                raise NotFoundException(
                    f"No encontré al médico {' '.join(words).title()} registrado. "
                    "Regístralo primero o dime un médico registrado."
                )

        # 2) Si no se dio nombre explícito, recién usar especialidad como fallback.
        if specialty:
            sp = self._norm(specialty)
            filtrados = [d for d in doctores if self._norm(d.specialty) == sp]
            if filtrados:
                return filtrados[0]

        # 3) Búsqueda general por nombre completo o tokens, evitando stopwords.
        words_text = [w for w in re.findall(r'\b[a-záéíóúñ]{3,}\b', text_norm) if w not in self._STOP_WORDS]
        for d in doctores:
            doc_words = set(self._norm(f"{d.first_name} {d.last_name}").split())
            if len(words_text) >= 2 and sum(1 for w in words_text if w in doc_words) >= 2:
                return d
            if len(words_text) == 1 and words_text[0] in doc_words:
                return d

        # 4) Fallback fonético.
        nombres_disponibles = [f"{d.first_name} {d.last_name}" for d in doctores]
        candidatos = set(words_text)
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
                return doctores[idx]

        raise NotFoundException("No se encontró al médico. Proporciona nombre completo o especialidad registrada.")

    def _es_solo_orden_crear_medico(self, text: str) -> bool:
        clean = text.lower().strip()
        ordenes = [
            "crear medico", "crear médico", "crear un medico", "crear un médico",
            "crear nuevo medico", "crear nuevo médico", "crear un nuevo medico", "crear un nuevo médico",
            "registrar medico", "registrar médico", "agregar medico", "agregar médico",
            "nuevo medico", "nuevo médico",
        ]
        return any(o in clean for o in ordenes) and "@" not in clean

    def prefill_doctor(self, text: str, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"

        # Si el usuario solo da la orden, NO extraer palabras de la orden como nombre.
        # Ejemplo incorrecto anterior: "crear un nuevo médico" => first_name="Nuevo".
        datos = {"first_name": "", "last_name": "", "specialty": "", "email": ""}
        if not self._es_solo_orden_crear_medico(text):
            datos = extraer_datos_medico(text)

        prefill = self._prefill_medico_es(datos)

        return {
            "type": "prefill",
            "action": "crear_medico",
            "target": "doctors",
            "message": (
                f"{nombre}, voy a guiarte paso a paso para crear el médico. "
                "Primero pediré nombres, luego apellidos, especialidad y correo real."
            ),
            "prefill": prefill,
        }

    def crear(self, text: str, user_name: str = "") -> dict:
        return self.prefill_doctor(text, user_name=user_name)

    def eliminar(self, text: str, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        try:
            doctor = self._buscar(text)
            self.service.eliminar_medico(doctor.id)
            return {
                "type": "success",
                "message": f"{nombre}, médico {doctor.first_name} {doctor.last_name} eliminado exitosamente.",
                "action": "eliminar_medico",
                "target": "doctors",
            }
        except NotFoundException as e:
            return {
                "type": "info",
                "message": str(e),
                "action": "eliminar_medico",
                "target": "doctors",
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error al eliminar médico: {str(e)}",
                "action": "eliminar_medico",
                "target": "doctors",
            }

    def listar(self, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        return {
            "type": "success",
            "message": f"{nombre}, te he llevado a la sección de médicos.\n¿Deseas **agregar**, **eliminar** o **actualizar** algún médico?",
            "action": "ver_medicos",
            "target": "doctors",
        }

    def consultar_especialidad(self, specialty: str, user_name: str = "") -> dict:
        nombre = user_name or "Usuario"
        doctores = self.service.listar_medicos()
        if specialty:
            filtrados = [d for d in doctores if d.specialty.lower() == specialty.lower()]
        else:
            filtrados = doctores

        if not filtrados:
            return {"type": "info", "message": "No hay médicos registrados.", "action": "consultar_doctor"}

        lines = ["Médicos disponibles:"]
        for d in filtrados[:10]:
            lines.append(f"  Dr. {d.first_name} {d.last_name} - {d.specialty}")
        return {"type": "success", "message": "\n".join(lines), "action": "consultar_doctor"}
