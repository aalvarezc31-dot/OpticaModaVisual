"""
Endpoints HTTP de la API.

    GET  /api/v1/                         estado del servidor y catálogo de operaciones
    POST /api/v1/sesion/                  login: usuario + contraseña -> token, rol, secciones
    POST /api/v1/<módulo>/<operación>/    ejecuta una operación de la capa de negocio

Cuerpo de una operación: {"args": [...], "kwargs": {...}}
Respuestas:
    200 {"resultado": ...}
    401 sin token o token vencido
    403 el rol no tiene permiso para esa sección
    404 operación no publicada o registro inexistente
    422 {"error": "regla_negocio", "mensaje": ..., "campo": ...}
"""
import inspect
import json
import logging

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from api import operaciones, token
from api.serializacion import a_json, desde_json
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError
from negocio.servicios import permisos, usuarios

log = logging.getLogger(__name__)


def _error(estado, codigo, mensaje, campo=None):
    return JsonResponse({"error": codigo, "mensaje": mensaje, "campo": campo}, status=estado)


def _cuerpo(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return None


@require_GET
def indice(request):
    """Estado del servidor y lista de operaciones publicadas."""
    return JsonResponse({
        "servicio": "Óptica Moda Visual · servidor de aplicación",
        "version": "v1",
        "operaciones": {
            modulo: {"seccion": seccion, "operaciones": sorted(publicadas)}
            for modulo, (_, seccion, publicadas) in operaciones.OPERACIONES.items()
        },
    })


@csrf_exempt
@require_POST
def iniciar_sesion(request):
    datos = _cuerpo(request) or {}
    user = authenticate(
        request,
        username=(datos.get("username") or "").strip(),
        password=datos.get("password") or "",
    )

    if user is None:
        return _error(401, "credenciales", "Usuario o contraseña incorrectos.")

    return JsonResponse({
        "token": token.emitir(user),
        "usuario": {
            "username": user.get_username(),
            "nombre": user.get_full_name() or user.get_username(),
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        },
        "rol": usuarios.rol_de_cuenta(user),
        "secciones": sorted(permisos.secciones_permitidas(user)),
    })


@csrf_exempt
@require_POST
def ejecutar(request, modulo, operacion):
    encabezado = request.headers.get("Authorization", "")
    user = token.usuario_del_token(encabezado.removeprefix("Token ").strip())
    if user is None:
        return _error(401, "no_autenticado", "La sesión venció. Vuelve a iniciar sesión.")

    encontrada = operaciones.buscar(modulo, operacion)
    if encontrada is None:
        return _error(404, "operacion_inexistente", f"La operación {modulo}.{operacion} no existe.")

    funcion, seccion, necesita_usuario = encontrada
    if not permisos.puede(user, seccion):
        return _error(403, "sin_permiso", "Tu rol no tiene acceso a esa sección.")

    cuerpo = _cuerpo(request)
    if cuerpo is None:
        return _error(400, "json_invalido", "El cuerpo de la petición no es JSON válido.")

    args = desde_json(cuerpo.get("args", []))
    kwargs = desde_json(cuerpo.get("kwargs", {}))
    if necesita_usuario:
        args = [user, *args]

    try:
        inspect.signature(funcion).bind(*args, **kwargs)
    except TypeError as error:
        log.warning("Argumentos inválidos para %s.%s: %s", modulo, operacion, error)
        return _error(400, "argumentos_invalidos", f"Argumentos inválidos para {modulo}.{operacion}.")

    try:
        resultado = funcion(*args, **kwargs)
    except ReglaNegocioError as error:
        return _error(422, "regla_negocio", error.mensaje, error.campo)
    except RecursoNoEncontrado as error:
        return _error(404, "no_encontrado", str(error))

    return JsonResponse({"resultado": a_json(resultado)})
