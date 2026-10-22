from django.http import Http404

from negocio.excepciones import RecursoNoEncontrado


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
