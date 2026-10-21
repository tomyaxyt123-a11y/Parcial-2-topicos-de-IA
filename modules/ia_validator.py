"""
Módulo de Inteligencia Artificial aplicada.

Contiene las técnicas inteligentes del proyecto:

1. **PLN (Procesamiento de Lenguaje Natural)** — normalización de nombres
   propios en español (tildes, capitalización, partículas, espacios).
2. **Similitud difusa (fuzzy matching)** — detección de duplicados por
   algoritmo de Levenshtein (`fuzzywuzzy`).
3. **PLN semántico** — mapeo de encabezados equivalentes
   (`"Email"`, `"e-mail"`, `"correo"` -> `correo`).
4. **Detección de anomalías** — correos inválidos, caracteres extraños y
   documentos con longitud atípica.

Si `spaCy` está instalado se utiliza como refuerzo para el tokenizado; de lo
contrario el sistema opera con el respaldo basado en reglas y similitud.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
from fuzzywuzzy import fuzz

# --------------------------------------------------------------------------
# 1. PLN: normalización de texto
# --------------------------------------------------------------------------

# Partículas que, en español, NO se capitalizan (salvo si son la primera
# palabra). Resuelve el caso borde "de la Torre" -> "De la Torre".
PARTICULAS_MINUSCULA = {
    "de", "del", "la", "las", "los", "y", "e", "da", "das", "do", "dos",
    "van", "von", "der", "den", "ter",
}

# Prefijos/apellidos compuestos que conservan su capitalización propia.
PARTICULAS_MAYUSCULA = {"mc", "mac", "san", "santa", "sancho", "st", "saint"}

# Prefijos que NO deben separarse al detectar mayúsculas internas
# ("McCarthy" no es "Mc Carthy").
PREFIJOS_NO_SEPARABLES = {"mc", "mac", "de", "del", "la", "van", "von", "san", "santa", "st", "saint", "o"}

# Patrones que indican capitalización interna que debe conservarse:
# "O'Neil", "McCarthy"
RE_CAPITAL_INTERNO = re.compile(r"[a-záéíóúñ][A-ZÁÉÍÓÚÑ]|['’][A-ZÁÉÍÓÚÑ]")


def normalizar_texto(texto: object) -> str:
    """Quita tildes, colapsa espacios y pasa a minúsculas.

    Es la operación base sobre la que se construyen las demás.
    """
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return ""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = unicodedata.normalize("NFD", texto.strip())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", texto).strip()


def _capitalizar_palabra(palabra: str) -> str:
    """Capitaliza una palabra conservando su capitalización interna."""
    if RE_CAPITAL_INTERNO.search(palabra):
        return palabra[:1].upper() + palabra[1:]
    return palabra[:1].upper() + palabra[1:].lower()


def _capitalizar_particulas(palabras: Sequence[str]) -> str:
    """Aplica Title Case respetando partículas del español."""
    resultado: List[str] = []
    for indice, palabra in enumerate(palabras):
        minuscula = palabra.lower()
        if indice > 0 and minuscula in PARTICULAS_MINUSCULA:
            resultado.append(minuscula)
        elif indice > 0 and minuscula in PARTICULAS_MAYUSCULA:
            resultado.append(minuscula[:1].upper() + minuscula[1:])
        else:
            resultado.append(_capitalizar_palabra(palabra))
    return " ".join(resultado)


def _separar_camel_case(texto: str) -> str:
    """Separa palabras pegadas: 'perezRodriguez' -> 'perez Rodriguez'.

    No separa cuando el primer fragmento es un prefijo conocido
    ('McCarthy' -> 'McCarthy').
    """
    resultado: List[str] = []
    for token in texto.split(" "):
        partes: List[str] = []
        for parte in re.split(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])", token):
            partes.extend(
                re.split(r"(?<=[A-ZÁÉÍÓÚÑ]{3})(?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])", parte)
            )
        # Recombina prefijos conocidos que no deben separarse
        while len(partes) > 1 and partes[0].lower() in PREFIJOS_NO_SEPARABLES:
            partes[0] = partes[0] + partes[1]
            partes.pop(1)
        resultado.append(" ".join(partes))
    return " ".join(resultado)


def normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre propio en español.

    Elimina tildes, capitaliza según reglas lingüísticas y unifica espacios.
    Ejemplos:
        "juan  perez "      -> "Juan Perez"
        "María José Pérez"  -> "Maria Jose Perez"
        "ana de la torres"  -> "Ana de la Torres"
        "perezRodriguez"    -> "Perez Rodriguez"
    """
    if nombre is None or (isinstance(nombre, float) and pd.isna(nombre)):
        return ""
    texto = normalizar_texto(nombre)
    if not texto:
        return ""
    texto = _separar_camel_case(texto)
    return _capitalizar_particulas(texto.split(" "))


def normalizar_nombre_completo(nombres: str, apellidos: str) -> str:
    """Construye el nombre completo normalizado a partir de dos campos."""
    return " ".join(p for p in (normalizar_nombre(nombres), normalizar_nombre(apellidos)) if p)


def normalizar_correo(correo: str) -> str:
    """Normaliza un correo: sin tildes, minúsculas y sin espacios."""
    texto = normalizar_texto(correo).lower().replace(" ", "")
    return texto


# --------------------------------------------------------------------------
# 2. Validación y detección de anomalías
# --------------------------------------------------------------------------

RE_CORREO = re.compile(r"^[\w\.\-\+]+@[\w\-]+(\.[\w\-]+)+$")
RE_CARACTERES_ESPECIALES = re.compile(r"[<>\"\{\}\|\^~\[\]`\\]", re.UNICODE)
RE_SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'\-]+$")

LONGITUDES_DOCUMENTO_VALIDAS = {5, 6, 7, 8, 9, 10, 11, 12}


def validar_correo_ia(correo: str) -> bool:
    """Valida el formato de un correo electrónico (semántica + reglas)."""
    if correo is None or (isinstance(correo, float) and pd.isna(correo)):
        return False
    correo = str(correo).strip()
    if not correo or len(correo) > 254:
        return False
    if not RE_CORREO.match(correo):
        return False
    local, _, dominio = correo.rpartition("@")
    if not local or len(local) > 64:
        return False
    if "." not in dominio or dominio.startswith("-") or dominio.endswith("-"):
        return False
    return True


def validar_documento(documento: str) -> bool:
    """Valida que un documento tenga longitud típica y solo dígitos."""
    if documento is None or (isinstance(documento, float) and pd.isna(documento)):
        return False
    texto = re.sub(r"[\s\.\-]", "", str(documento))
    if not texto.isdigit():
        return False
    return len(texto) in LONGITUDES_DOCUMENTO_VALIDAS


def detectar_anomalias(registro: Dict[str, object]) -> List[str]:
    """Detecta anomalías en un registro de participante.

    Devuelve una lista de descripciones legibles; lista vacía = sin anomalías.
    """
    anomalias: List[str] = []

    nombre = registro.get("nombres", "")
    apellidos = registro.get("apellidos", "")
    correo = registro.get("correo", "")
    documento = registro.get("documento", "")

    if not str(nombre or "").strip():
        anomalias.append("Nombre vacío")

    if str(nombre or "").strip() and not RE_SOLO_LETRAS.match(str(nombre)):
        anomalias.append("El nombre contiene caracteres no alfabéticos")

    if str(apellidos or "").strip() and not RE_SOLO_LETRAS.match(str(apellidos)):
        anomalias.append("Los apellidos contienen caracteres no alfabéticos")

    if not validar_correo_ia(correo):
        anomalias.append(f"Correo inválido: {correo or '(vacío)'}")

    if str(correo or "").strip() and RE_CARACTERES_ESPECIALES.search(str(correo)):
        anomalias.append("El correo contiene caracteres especiales sospechosos")

    if documento is not None and str(documento).strip():
        if not validar_documento(documento):
            anomalias.append(f"Documento con formato o longitud atípica: {documento}")

    return anomalias


# --------------------------------------------------------------------------
# 3. Mapeo semántico de encabezados
# --------------------------------------------------------------------------

# Diccionario de sinónimos canónicos por campo del modelo de datos.
SINONIMOS_CAMPOS: Dict[str, set] = {
    "nombres": {
        "nombre", "nombres", "name", "firstname", "firstname", "nombre1",
        "primer nombre", "nombres del participante", "nombres y apellidos",
    },
    "apellidos": {
        "apellido", "apellidos", "apellidos del participante", "surname",
        "lastname", "last name", "apellido1", "familia",
    },
    "correo": {
        "correo", "email", "e mail", "mail", "correo electronico",
        "correo institucional", "direccion de correo", "direccion email",
        "correo electronico institucional", "email institucional",
    },
    "documento": {
        "documento", "documento de identidad", "numero de documento", "cc",
        "cedula", "cedula de ciudadania", "dni", "id", "nit", "num doc",
    },
    "ponencia": {
        "ponencia", "titulo de la ponencia", "titulo ponencia", "titulo",
        "tema", "talk", "title", "nombre de la ponencia", "ponencia taller",
    },
    "conferencia": {
        "conferencia", "charla", "keynote", "titulo de la conferencia",
        "titulo conferencia", "nombre de la conferencia", "plenaria",
    },
    "institucion": {
        "institucion", "entidad", "empresa", "universidad", "afiliacion",
        "organizacion", "companía", "compania",
    },
    "cargo": {"cargo", "rol", "puesto", "posicion", "titulo laboral"},
}


def _clave_columna(columna: object) -> str:
    """Reduce un encabezado a una clave comparable (sin tildes ni símbolos)."""
    texto = normalizar_texto(columna).lower()
    texto = texto.replace("_", " ").replace("-", " ").replace(".", " ")
    texto = re.sub(r"[()\[\]:;,/\\]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


@lru_cache(maxsize=1)
def _indice_sinonimos() -> Dict[str, str]:
    """Índice inverso `sinónimo -> campo canónico`.

    Los nombres canónicos se registran primero para que siempre tengan
    prioridad sobre un alias equivalente (p. ej. `ponencia` es un campo
    canónico y no un alias de `conferencia`).
    """
    indice: Dict[str, str] = {}
    for canonico in SINONIMOS_CAMPOS:
        indice[_clave_columna(canonico)] = canonico
    for canonico, alias in SINONIMOS_CAMPOS.items():
        for alias in alias:
            clave = _clave_columna(alias)
            indice.setdefault(clave, canonico)
    return indice


def mapear_encabezados(columnas: Iterable[object], umbral: int = 85) -> Dict[str, str]:
    """Mapea encabezados arbitrarios a los campos canónicos del modelo.

    Estrategia híbrida:
        1. Coincidencia exacta contra el diccionario de sinónimos.
        2. Coincidencia difusa (`fuzz.ratio`) con umbral configurable.

    Devuelve un diccionario `{columna_original: campo_canonico}` con la
    correspondencia detectada.
    """
    indice = _indice_sinonimos()
    mapeo: Dict[str, str] = {}
    usados: set = set()

    columnas_lista = list(columnas)

    # Paso 1: coincidencia exacta (prioridad alta, sin ambigüedad).
    for columna in columnas_lista:
        clave = _clave_columna(columna)
        if clave in indice:
            canonico = indice[clave]
            if canonico not in usados:
                mapeo[str(columna)] = canonico
                usados.add(canonico)

    # Paso 2: coincidencia difusa para los encabezados no resueltos.
    for columna in columnas_lista:
        if str(columna) in mapeo:
            continue
        clave = _clave_columna(columna)
        if not clave:
            continue
        mejor_canonico, mejor_puntaje = None, 0.0
        for alias, canonico in indice.items():
            if canonico in usados:
                continue
            puntaje = fuzz.ratio(clave, alias)
            if puntaje > mejor_puntaje:
                mejor_canonico, mejor_puntaje = canonico, puntaje
        if mejor_canonico is not None and mejor_puntaje >= umbral:
            mapeo[str(columna)] = mejor_canonico
            usados.add(mejor_canonico)

    return mapeo


def detectar_columna_canonica(columnas: Iterable[object], canonico: str) -> Optional[str]:
    """Devuelve el encabezado original que corresponde a un campo canónico."""
    for original, mapeado in mapear_encabezados(columnas).items():
        if mapeado == canonico:
            return original
    return None


# --------------------------------------------------------------------------
# 4. Detección de duplicados (similitud difusa / Levenshtein)
# --------------------------------------------------------------------------


def detectar_duplicados(
    df: pd.DataFrame,
    umbral: int = 90,
    columna: str = "correo",
) -> List[Tuple[int, int, float]]:
    """Detecta registros duplicados o casi duplicados dentro de una hoja.

    Devuelve una lista de tuplas `(i, j, puntaje)` donde `i < j` son los
    índices de las filas y `puntaje` el porcentaje de similitud
    (algoritmo de Levenshtein de `fuzzywuzzy`).
    """
    if df is None or df.empty or columna not in df.columns:
        return []

    valores = df[columna].fillna("").astype(str).map(normalizar_correo).tolist()
    duplicados: List[Tuple[int, int, float]] = []
    for i in range(len(valores)):
        if not valores[i]:
            continue
        for j in range(i + 1, len(valores)):
            if not valores[j]:
                continue
            puntaje = fuzz.ratio(valores[i], valores[j])
            if puntaje >= umbral:
                duplicados.append((i, j, float(puntaje)))
    return duplicados


def detectar_duplicados_por_nombre(
    df: pd.DataFrame,
    umbral: int = 90,
) -> List[Tuple[int, int, float]]:
    """Detecta duplicados combinando nombres y apellidos."""
    if df is None or df.empty:
        return []
    if "nombres" not in df.columns or "apellidos" not in df.columns:
        return []

    nombres = df["nombres"].fillna("").map(normalizar_nombre).tolist()
    apellidos = df["apellidos"].fillna("").map(normalizar_nombre).tolist()
    completos = [f"{n} {a}".strip() for n, a in zip(nombres, apellidos)]

    duplicados: List[Tuple[int, int, float]] = []
    for i in range(len(completos)):
        if not completos[i]:
            continue
        for j in range(i + 1, len( completos)):
            if not completos[j]:
                continue
            puntaje = fuzz.ratio(completos[i], completos[j])
            if puntaje >= umbral:
                duplicados.append((i, j, float(puntaje)))
    return duplicados


def resumir_duplicados(
    duplicados: Sequence[Tuple[int, int, float]],
    df: pd.DataFrame,
    columna: str = "correo",
) -> List[Dict[str, object]]:
    """Convierte las tuplas de duplicados en reportes legibles por rol."""
    resumen: List[Dict[str, object]] = []
    for i, j, puntaje in duplicados:
        resumen.append(
            {
                "fila_a": int(i),
                "fila_b": int(j),
                "valor_a": str(df.iloc[i].get(columna, "")) if i < len(df) else "",
                "valor_b": str(df.iloc[j].get(columna, "")) if j < len(df) else "",
                "similitud": round(puntaje, 2),
            }
        )
    return resumen


# --------------------------------------------------------------------------
# 5. Refuerzo opcional con spaCy
# --------------------------------------------------------------------------

_NLP = None
_NLP_CARGADO = False


@lru_cache(maxsize=1)
def _cargar_nlp():
    """Carga el pipeline de spaCy en español si está disponible."""
    global _NLP, _NLP_CARGADO
    if _NLP_CARGADO:
        return _NLP
    _NLP_CARGADO = True
    try:  # pragma: no cover - depende del entorno
        import spacy

        try:
            _NLP = spacy.load("es_core_news_sm")
        except OSError:
            _NLP = spacy.blank("es")
    except Exception:
        _NLP = None
    return _NLP


def pln_disponible() -> bool:
    """Indica si spaCy está operativo en el entorno."""
    return _cargar_nlp() is not None


def tokenizar_nombre(nombre: str) -> List[str]:
    """Tokeniza un nombre; usa spaCy si está disponible y regex como respaldo."""
    texto = normalizar_texto(nombre)
    if not texto:
        return []
    nlp = _cargar_nlp()
    if nlp is not None:
        doc = nlp(texto)
        tokens = [t.text for t in doc if not t.is_space and not t.is_punct]
        if tokens:
            return tokens
    return [t for t in re.split(r"[^\w'\-]+", texto) if t]


def parecer_nombre_propio(texto: str) -> bool:
    """Estima si un texto parece un nombre propio (heurística PLN)."""
    tokens = tokenizar_nombre(texto)
    if not tokens:
        return False
    if len(tokens) > 5:
        return False
    return all(t[:1].isupper() or t.lower() in PARTICULAS_MINUSCULA for t in tokens)
