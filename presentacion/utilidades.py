"""Ayudas comunes para las vistas."""
from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator

POR_PAGINA = 15


def paginar(request, registros, por_pagina=POR_PAGINA):
    """
    Devuelve la página pedida (?pagina=N) y la query string sin `pagina`,
    para que los enlaces de paginación conserven los filtros.
    """
    pagina = Paginator(registros, por_pagina).get_page(request.GET.get("pagina"))
    parametros = request.GET.copy()
    parametros.pop("pagina", None)

    return {
        "pagina": pagina,
        "filtros_query": parametros.urlencode(),
    }


def fecha_de_query(request, nombre="fecha"):
    try:
        return date.fromisoformat(request.GET.get(nombre, ""))
    except ValueError:
        return None


def mostrar_error(request, form, error):
    """Muestra un ReglaNegocioError en su campo o como mensaje general."""
    if error.campo and form is not None and error.campo in form.fields:
        form.add_error(error.campo, error.mensaje)
    else:
        messages.error(request, error.mensaje)
