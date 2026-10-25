"""
Validaciones de formato que la capa de negocio aplica SIEMPRE, aunque el
servidor web ya las haya hecho (nadie puede saltarlas llamando a la API).
"""
import re

from negocio.excepciones import ReglaNegocioError

# Teléfono: dígitos con espacios, guiones, paréntesis y un + inicial opcional.
# Entre 8 (número de Guatemala) y 15 dígitos (máximo internacional E.164).
TELEFONO_MIN_DIGITOS = 8
TELEFONO_MAX_DIGITOS = 15
RE_TELEFONO = re.compile(r"^\+?[0-9\s\-()]+$")

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Referencia de voucher / boleta: exclusivamente dígitos.
RE_VOUCHER = re.compile(r"^[0-9]+$")
VOUCHER_MAX = 60


def texto_obligatorio(valor, campo, etiqueta, maximo=None):
    texto = (valor or "").strip()
    if not texto:
        raise ReglaNegocioError(f"{etiqueta} es obligatorio.", campo=campo)
    if maximo and len(texto) > maximo:
        raise ReglaNegocioError(f"{etiqueta} admite como máximo {maximo} caracteres.", campo=campo)
    return texto


def telefono(valor, campo="telefono"):
    """Devuelve el teléfono limpio o None si viene vacío."""
    texto = (valor or "").strip()
    if not texto:
        return None

    digitos = sum(c.isdigit() for c in texto)
    if not RE_TELEFONO.fullmatch(texto) or not TELEFONO_MIN_DIGITOS <= digitos <= TELEFONO_MAX_DIGITOS:
        raise ReglaNegocioError(
            f"El teléfono debe tener entre {TELEFONO_MIN_DIGITOS} y {TELEFONO_MAX_DIGITOS} dígitos "
            "(se permiten espacios, guiones, paréntesis y + inicial).",
            campo=campo,
        )
    return texto


def email(valor, campo="email"):
    texto = (valor or "").strip()
    if not texto:
        return None
    if not RE_EMAIL.fullmatch(texto):
        raise ReglaNegocioError("Ingresa un correo válido, por ejemplo nombre@dominio.com.", campo=campo)
    return texto


def voucher(valor, campo="referencia"):
    """Referencia de pago: vacía o solo dígitos."""
    texto = (valor or "").strip()
    if not texto:
        return None
    if not RE_VOUCHER.fullmatch(texto) or len(texto) > VOUCHER_MAX:
        raise ReglaNegocioError("La referencia del voucher solo admite números.", campo=campo)
    return texto
