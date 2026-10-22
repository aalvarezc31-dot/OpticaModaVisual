from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from negocio.servicios import panel


@login_required
def inicio(request):
    return render(request, "presentacion/inicio.html", panel.resumen_inicio())
