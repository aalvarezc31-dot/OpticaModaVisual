from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

from presentacion import sesion
from presentacion.cliente_api import (
    RecursoNoEncontrado, ServidorNoDisponible, SesionVencida, SinPermiso, token_actual,
)
from presentacion.context_processors import seccion_de_ruta


class SesionAPIMiddleware:
    """Arma request.user desde la cookie de sesión y deja el token listo para la API."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = sesion.usuario_de(request)
        marca = token_actual.set(request.user.token)
        try:
            return self.get_response(request)
        finally:
            token_actual.reset(marca)


class ErroresAPIMiddleware:
    """Traduce los errores de la API a respuestas para el navegador."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, RecursoNoEncontrado):
            raise Http404(exception.mensaje)

        if isinstance(exception, SesionVencida):
            sesion.cerrar(request)
            messages.info(request, "Tu sesión venció. Vuelve a iniciar sesión.")
            return redirect("login")

        if isinstance(exception, SinPermiso):
            messages.error(request, exception.mensaje)
            return redirect("inicio")

        if isinstance(exception, ServidorNoDisponible):
            return render(request, "presentacion/servidor_no_disponible.html",
                          {"detalle": exception.mensaje}, status=503)

        return None


class PermisosPorRolMiddleware:
    """
    Oculta al navegador las secciones que el rol no puede usar.
    (La API vuelve a validar el permiso en cada operación.)
    """

    RUTAS_LIBRES = ("/login/", "/logout/", "/static/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith(self.RUTAS_LIBRES):
            seccion = seccion_de_ruta(request.path)

            if seccion and seccion not in request.user.secciones:
                messages.error(request, "Tu rol no tiene acceso a esa sección.")
                return redirect("inicio")

        return self.get_response(request)
