from django.contrib import messages
from django.http import Http404
from django.shortcuts import render

from presentacion.cliente_api import ReglaNegocioError
from presentacion.exportar import respuesta_csv, respuesta_xlsx
from presentacion.servicios import reportes
from presentacion.sesion import login_required
from presentacion.utilidades import fecha_de_query


def _filtro(request):
    """Rango del formulario (?desde=AAAA-MM-DD&hasta=AAAA-MM-DD) o un periodo rápido (?dias=N)."""
    return {
        "desde": fecha_de_query(request, "desde"),
        "hasta": fecha_de_query(request, "hasta"),
        "dias": request.GET.get("dias"),
    }


@login_required
def reportes_generales(request):
    """Dashboard analítico: indicadores, gráficas interactivas y reportes exportables."""
    try:
        contexto = reportes.tablero(**_filtro(request))
    except ReglaNegocioError as error:
        messages.error(request, error.mensaje)
        contexto = reportes.tablero()
    return render(request, "presentacion/reportes.html", contexto)


@login_required
def exportar_reporte(request, nombre):
    """Descarga un reporte en Excel (?formato=xlsx, por defecto) o CSV (?formato=csv)."""
    try:
        resultado = reportes.exportacion(nombre, **_filtro(request))
    except ReglaNegocioError as error:
        raise Http404(error.mensaje)
    if resultado is None:
        raise Http404("Ese reporte no existe.")

    titulo, encabezados, filas = resultado
    if request.GET.get("formato") == "csv":
        return respuesta_csv(titulo, encabezados, filas)

    filtro = _filtro(request)
    periodo = (f"Del {filtro['desde']:%d/%m/%Y} al {filtro['hasta']:%d/%m/%Y}"
               if filtro["desde"] and filtro["hasta"] else "")
    return respuesta_xlsx(titulo, encabezados, filas, subtitulo=periodo)
