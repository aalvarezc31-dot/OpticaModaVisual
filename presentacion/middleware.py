from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect

from negocio.excepciones import RecursoNoEncontrado
from presentacion.context_processors import seccion_de_ruta, secciones_del_usuario


class RecursoNoEncontradoMiddleware:
    """Convierte RecursoNoEncontrado (capa de negocio) en una página 404."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, RecursoNoEncontrado):
            raise Http404(str(exception))
        return None


class PermisosPorRolMiddleware:
    """
    Bloquea las secciones que el rol del usuario no puede usar
    (ver negocio/servicios/permisos.py), aunque escriba la URL a mano.
    """

    RUTAS_LIBRES = ("/login/", "/logout/", "/admin/", "/static/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated
                and not request.path.startswith(self.RUTAS_LIBRES)):
            seccion = seccion_de_ruta(request.path)

            if seccion and seccion not in secciones_del_usuario(request):
                messages.error(request, "Tu rol no tiene acceso a esa sección.")
                return redirect("inicio")

        return self.get_response(request)
