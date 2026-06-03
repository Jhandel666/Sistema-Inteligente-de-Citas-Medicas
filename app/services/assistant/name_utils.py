from __future__ import annotations

import difflib
import re

_VARIANTES_LETRA = {
    "j": ["y", "h"],
    "y": ["j", "ll"],
    "h": ["j", "y"],
    "v": ["b"],
    "b": ["v"],
    "z": ["s"],
    "s": ["z"],
    "c": ["s", "z", "k"],
    "ll": ["y"],
    "g": ["j"],
    "k": ["c", "q"],
    "q": ["c", "k"],
    "x": ["s", "j"],
}

_LETRAS_ES = {
    "jota": "j", "hache": "h", "a": "a", "be": "b", "be larga": "b",
    "ce": "c", "de": "d", "e": "e", "efe": "f", "ge": "g",
    "i": "i", "ka": "k", "ele": "l", "eme": "m", "ene": "n",
    "eñe": "ñ", "o": "o", "pe": "p", "cu": "q", "erre": "r",
    "ese": "s", "te": "t", "u": "u", "ve": "v", "uve": "v",
    "ve corta": "v", "uve doble": "w", "doble u": "w",
    "equis": "x", "ye": "y", "i griega": "y", "zeta": "z",
}


def reconstruir_nombre_deletreado(text: str) -> str | None:
    """Detecta nombre deletreado letra por letra y lo reconstruye.

    Patrones:
      "J H A N D E L"   (mayúsculas separadas)
      "J-H-A-N-D-E-L"   (con guiones)
      "J, H, A, N, D, E, L"
      "jota hache a ene de e ele"  (nombre español de las letras)
    """
    # Letras sueltas (mayúsculas/minúsculas separadas por espacios, guiones o comas)
    m = re.search(r'(?:^|[\s,.(])((?:[a-zA-Z][\s,\-–—]){2,}[a-zA-Z])(?:\s*$|[\s),.])', text)
    if m:
        letters = re.findall(r'[a-zA-Z]', m.group(1))
        if len(letters) >= 3:
            return "".join(letters).lower()

    # Nombres de letras en español: "jota hache a ene de e ele"
    letras = []
    for token in re.findall(r'[a-záéíóúñ]+', text.lower()):
        if token in _LETRAS_ES:
            letras.append(_LETRAS_ES[token])
    if len(letras) >= 3:
        return "".join(letras)

    return None


def aplicar_correccion_letra(text: str, nombre_base: str | None = None) -> str | None:
    """Detecta correcciones tipo 'con J', 'con H', 'como H' y las aplica.

    Ej: Texto: 'Yandel con J'  →  nombre_base='yandel', letra='j' → 'jhandel'
        Texto: 'se escribe con J' → busca en nombre_base o en palabras previas
    """
    m = re.search(r'(?:con|como)\s+(la\s+)?([a-zA-Z])', text)
    if not m:
        return None
    letra_correcta = m.group(2).lower()

    if nombre_base:
        # Reemplazar primera letra o la letra fonéticamente similar
        nombre = nombre_base.lower()
        if nombre and nombre[0] != letra_correcta:
            # Verificar que la primera letra sea una confusión típica
            if nombre[0] in _VARIANTES_LETRA.get(letra_correcta, []):
                return letra_correcta + nombre[1:]
    return None


def generar_variantes_foneticas(nombre: str) -> set[str]:
    """Genera posibles transcripciones erróneas de voz para un nombre."""
    nombre = nombre.lower().strip()
    if not nombre:
        return set()

    variantes = {nombre}

    for i, letra in enumerate(nombre):
        if letra in _VARIANTES_LETRA:
            for alt in _VARIANTES_LETRA[letra]:
                variantes.add(nombre[:i] + alt + nombre[i + 1:])

    # Quitar una letra (por si el voz la omitió o agregó)
    for i in range(len(nombre)):
        if len(nombre) > 2:
            variantes.add(nombre[:i] + nombre[i + 1:])

    return variantes


def coincidencia_fuzzy(query: str, candidatos: list[str], threshold: float = 0.6) -> tuple[str | None, float]:
    """Encuentra el mejor match por SequenceMatcher entre query y candidatos."""
    query = query.lower().strip()
    if not query or not candidatos:
        return None, 0.0

    mejor: str | None = None
    mejor_score = 0.0

    for c in candidatos:
        score = difflib.SequenceMatcher(None, query, c.lower()).ratio()
        if score > mejor_score:
            mejor_score = score
            mejor = c

    return (mejor, mejor_score) if mejor_score >= threshold else (None, mejor_score)


def buscar_por_nombre_fonetico(query: str, nombres_completos: list[str]) -> str | None:
    """Busca el nombre más parecido a query usando fuzzy + variantes fonéticas.

    Compara contra el nombre completo y también contra cada palabra individual
    (nombre, apellido) para capturar errores de voz sin falsos positivos.
    """
    deletreado = reconstruir_nombre_deletreado(query)
    busquedas = {query.lower()}

    if deletreado:
        busquedas.add(deletreado)
        busquedas.update(generar_variantes_foneticas(deletreado))

    busquedas.update(generar_variantes_foneticas(query))

    for p in re.findall(r'\b[a-záéíóúñ]{3,}\b', query.lower()):
        busquedas.add(p)

    mejor_global: str | None = None
    mejor_score_global = 0.0

    # Pre-calcular palabras individuales de cada candidato
    nombres_partes: list[tuple[str, list[str]]] = [
        (n, n.lower().split()) for n in nombres_completos
    ]

    for bq in busquedas:
        # Match contra nombre completo
        match, score = coincidencia_fuzzy(bq, nombres_completos, threshold=0.0)
        if match and score > mejor_score_global:
            mejor_score_global = score
            mejor_global = match

        # Match contra cada parte individual (nombre, apellido) con threshold más alto
        for nombre_completo, partes in nombres_partes:
            for parte in partes:
                if len(parte) < 3:
                    continue
                pr = difflib.SequenceMatcher(None, bq, parte).ratio()
                if pr > mejor_score_global and pr >= 0.8:
                    mejor_score_global = pr
                    mejor_global = nombre_completo

    if (not mejor_global or mejor_score_global < 0.5) and deletreado:
        corregido = aplicar_correccion_letra(query, deletreado)
        if corregido:
            match, score = coincidencia_fuzzy(corregido, nombres_completos)
            if match:
                return match
        if deletreado:
            match, score = coincidencia_fuzzy(deletreado, nombres_completos)
            if match:
                return match

    if mejor_global and mejor_score_global >= 0.75:
        return mejor_global

    return None
