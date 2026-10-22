from django.contrib import messages
from django.shortcuts import redirect, render

from negocio.servicios import autenticacion


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        valido = autenticacion.iniciar_sesion(
            request,
            request.POST.get("username", ""),
            request.POST.get("password", ""),
        )

        if valido:
            return redirect("inicio")

        messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "presentacion/login.html")


def cerrar_sesion(request):
    if request.method == "POST":
        autenticacion.cerrar_sesion(request)
        return redirect("login")

    return redirect("inicio")
