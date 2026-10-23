from django.http import Http404
from django.shortcuts import render

from presentacion.exportar import respuesta_csv, respuesta_xlsx
from presentacion.servicios import reportes
from presentacion.sesion import login_required

PERIODOS = (7, 30, 90, 365)


def _dias(request):
    try:
        dias = int(request.GET.get("dias", 30))
    except ValueError:
        return 30
    return dias if dias in PERIODOS else 30


@login_required
def reportes_generales(request):
    """Dashboard analítico: indicadores, gráficas interactivas y reportes exportables."""
    return render(request, "presentacion/reportes.html", reportes.tablero(_dias(request)))


@login_required
def exportar_reporte(request, nombre):
    """Descarga un reporte en Excel (?formato=xlsx, por defecto) o CSV (?formato=csv)."""
    dias = _dias(request)
    resultado = reportes.exportacion(nombre, dias)
    if resultado is None:
        raise Http404("Ese reporte no existe.")

    titulo, encabezados, filas = resultado
    if request.GET.get("formato") == "csv":
        return respuesta_csv(titulo, encabezados, filas)

    return respuesta_xlsx(titulo, encabezados, filas, subtitulo=f"Periodo: últimos {dias} días")
