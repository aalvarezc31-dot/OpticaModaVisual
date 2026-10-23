"""
Cliente HTTP del servidor de aplicación (nivel 2).

Es la ÚNICA forma en que el servidor web obtiene o guarda datos: no tiene
acceso a la base de datos ni importa código de la capa de negocio.

    from presentacion.servicios import clientes
    clientes.buscar("Ana")   ->  POST {API}/api/v1/clientes/buscar/  {"args": ["Ana"]}
"""
import contextvars
import json
import urllib.error
import urllib.request
from datetime import date, datetime, time
from decimal import Decimal

from django.conf import settings

# Token de la petición en curso (lo coloca SesionAPIMiddleware).
token_actual = contextvars.ContextVar("token_api", default=None)


# --- Errores que la API puede devolver ---

class ErrorAPI(Exception):
    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


class ReglaNegocioError(ErrorAPI):
    """422: la operación viola una regla del negocio (se muestra al usuario)."""


class RecursoNoEncontrado(ErrorAPI):
    """404: el registro no existe."""


class SinPermiso(ErrorAPI):
    """403: el rol del usuario no tiene acceso a esa sección."""


class SesionVencida(ErrorAPI):
    """401: no hay token o venció."""


class ServidorNoDisponible(ErrorAPI):
    """El servidor de aplicación no responde."""


ERRORES_POR_ESTADO = {
    401: SesionVencida,
    403: SinPermiso,
    404: RecursoNoEncontrado,
    422: ReglaNegocioError,
}


# --- Datos que viajan ---

class Registro(dict):
    """Un registro recibido de la API: se lee como objeto (r.nombre) o como dict."""

    def __getattr__(self, nombre):
        try:
            return self[nombre]
        except KeyError:
            raise AttributeError(nombre) from None

    def __setattr__(self, nombre, valor):
        self[nombre] = valor


def codificar(valor):
    if isinstance(valor, Decimal):
        return {"$decimal": str(valor)}
    if isinstance(valor, datetime):
        return {"$fechahora": valor.isoformat()}
    if isinstance(valor, date):
        return {"$fecha": valor.isoformat()}
    if isinstance(valor, time):
        return {"$hora": valor.isoformat()}
    if isinstance(valor, dict):
        return {str(k): codificar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple, set, frozenset)):
        return [codificar(v) for v in valor]
    return valor


def decodificar(valor):
    if isinstance(valor, list):
        return [decodificar(v) for v in valor]
    if isinstance(valor, dict):
        if len(valor) == 1:
            (marca, texto), = valor.items()
            if marca == "$decimal":
                return Decimal(texto)
            if marca == "$fecha":
                return date.fromisoformat(texto)
            if marca == "$fechahora":
                return datetime.fromisoformat(texto)
            if marca == "$hora":
                return time.fromisoformat(texto)
        return Registro({k: decodificar(v) for k, v in valor.items()})
    return valor


# --- Peticiones ---

def _post(ruta, cuerpo, token=None):
    url = settings.URL_API.rstrip("/") + ruta
    encabezados = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        encabezados["Authorization"] = f"Token {token}"

    peticion = urllib.request.Request(
        url, data=json.dumps(cuerpo).encode("utf-8"), headers=encabezados, method="POST"
    )

    try:
        with urllib.request.urlopen(peticion, timeout=settings.API_TIMEOUT) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            datos = json.loads(error.read().decode("utf-8"))
        except ValueError:
            datos = {}
        clase = ERRORES_POR_ESTADO.get(error.code, ErrorAPI)
        raise clase(datos.get("mensaje") or f"Error {error.code} del servidor de aplicación.",
                    datos.get("campo")) from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        raise ServidorNoDisponible(
            f"El servidor de aplicación ({settings.URL_API}) no responde."
        ) from error


def llamar(modulo, operacion, *args, **kwargs):
    respuesta = _post(
        f"/api/v1/{modulo}/{operacion}/",
        {"args": codificar(list(args)), "kwargs": codificar(kwargs)},
        token=token_actual.get(),
    )
    return decodificar(respuesta.get("resultado"))


def iniciar_sesion(username, password):
    """Devuelve {token, usuario, rol, secciones} o lanza SesionVencida si no son válidas."""
    return decodificar(_post("/api/v1/sesion/", {"username": username, "password": password}))


class Modulo:
    """Representa un módulo de la API: `clientes.buscar(...)` llama a clientes/buscar."""

    def __init__(self, nombre):
        self._nombre = nombre

    def __getattr__(self, operacion):
        if operacion.startswith("_"):
            raise AttributeError(operacion)
        return lambda *args, **kwargs: llamar(self._nombre, operacion, *args, **kwargs)

    def __repr__(self):
        return f"<módulo de la API '{self._nombre}'>"
