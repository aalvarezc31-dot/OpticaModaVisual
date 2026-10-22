from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from negocio.servicios import reportes


@login_required
def reportes_generales(request):
    try:
        dias = int(request.GET.get("dias", 30))
    except ValueError:
        dias = 30

    dias = dias if dias in (7, 30, 90, 365) else 30

    return render(request, "presentacion/reportes.html", reportes.resumen(dias))
