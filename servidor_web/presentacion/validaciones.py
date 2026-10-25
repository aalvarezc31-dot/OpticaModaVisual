"""
Validaciones de formato del lado del servidor web y atributos HTML para que
el navegador también las aplique. La API repite estas mismas reglas.
"""
import re

from django import forms

TELEFONO_MIN_DIGITOS = 8
TELEFONO_MAX_DIGITOS = 15
RE_TELEFONO = re.compile(r"^\+?[0-9\s\-()]+$")
RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_VOUCHER = re.compile(r"^[0-9]+$")

# Atributos para los <input> (validación en el navegador).
ATTRS_TELEFONO = {
    "type": "tel", "inputmode": "tel", "minlength": str(TELEFONO_MIN_DIGITOS), "maxlength": "20",
    "pattern": r"\+?[0-9\s\-()]{8,20}", "placeholder": "Ej. 5555-1234",
    "title": f"Entre {TELEFONO_MIN_DIGITOS} y {TELEFONO_MAX_DIGITOS} dígitos",
}
ATTRS_EMAIL = {
    "pattern": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "placeholder": "nombre@dominio.com", "title": "Correo con el formato nombre@dominio.com",
}
ATTRS_VOUCHER = {
    "inputmode": "numeric", "pattern": "[0-9]+", "maxlength": "60",
    "placeholder": "Solo números", "title": "La referencia del voucher solo admite números",
}


def limpiar_telefono(valor):
    texto = (valor or "").strip()
    if not texto:
        return None
    digitos = sum(c.isdigit() for c in texto)
    if not RE_TELEFONO.fullmatch(texto) or not TELEFONO_MIN_DIGITOS <= digitos <= TELEFONO_MAX_DIGITOS:
        raise forms.ValidationError(
            f"El teléfono debe tener entre {TELEFONO_MIN_DIGITOS} y {TELEFONO_MAX_DIGITOS} dígitos."
        )
    return texto


def limpiar_email(valor):
    texto = (valor or "").strip()
    if not texto:
        return None
    if not RE_EMAIL.fullmatch(texto):
        raise forms.ValidationError("Ingresa un correo válido, por ejemplo nombre@dominio.com.")
    return texto


def limpiar_voucher(valor):
    texto = (valor or "").strip()
    if not texto:
        return None
    if not RE_VOUCHER.fullmatch(texto):
        raise forms.ValidationError("La referencia del voucher solo admite números.")
    return texto


def texto_obligatorio(valor, mensaje):
    texto = (valor or "").strip()
    if not texto:
        raise forms.ValidationError(mensaje)
    return texto
