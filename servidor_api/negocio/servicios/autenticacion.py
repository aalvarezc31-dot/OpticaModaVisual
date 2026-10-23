from django.contrib.auth import authenticate, login, logout


def iniciar_sesion(request, username, password):
    """Devuelve True si las credenciales son validas y abre la sesion."""
    usuario = authenticate(
        request,
        username=username.strip(),
        password=password
    )

    if usuario is None:
        return False

    login(request, usuario)
    return True


def cerrar_sesion(request):
    logout(request)
