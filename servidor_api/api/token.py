"""
Token de acceso que el servidor web envía en cada petición
(cabecera `Authorization: Token <token>`).

Es el id del usuario firmado con la SECRET_KEY de este servidor:
el servidor web no puede fabricarlo ni modificarlo.
"""
from django.contrib.auth import get_user_model
from django.core import signing

SAL = "optica-moda-visual.api"
DURACION_SEGUNDOS = 12 * 60 * 60  # una jornada


def emitir(user):
    return signing.TimestampSigner(salt=SAL).sign(str(user.pk))


def usuario_del_token(token):
    """Devuelve el usuario activo dueño del token, o None si es inválido o venció."""
    try:
        id_usuario = signing.TimestampSigner(salt=SAL).unsign(token, max_age=DURACION_SEGUNDOS)
    except signing.BadSignature:
        return None

    return get_user_model().objects.filter(pk=id_usuario, is_active=True).first()
