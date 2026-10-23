from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from presentacion import cliente_api, sesion


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        try:
            datos = cliente_api.iniciar_sesion(
                request.POST.get("username", "").strip(),
                request.POST.get("password", ""),
            )
        except cliente_api.SesionVencida:
            messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            sesion.guardar(request, datos)
            siguiente = request.GET.get("next", "")
            if url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
                return redirect(siguiente)
            return redirect("inicio")

    return render(request, "presentacion/login.html")


def cerrar_sesion(request):
    if request.method == "POST":
        sesion.cerrar(request)
        return redirect("login")

    return redirect("inicio")
