from datos.models import Rol, Usuario


def listar_activos():
    return Usuario.objects.filter(activo=True).order_by("nombres")


def obtener_activo(id_usuario):
    return Usuario.objects.get(pk=id_usuario, activo=True)


def obtener_por_username(username):
    """Usuario de seguridad.usuario con el mismo username que el login de Django."""
    return Usuario.objects.filter(username__iexact=username, activo=True).first()


def buscar_por_username(username):
    """Igual que obtener_por_username pero incluye inactivos."""
    return Usuario.objects.filter(username__iexact=username).first()


def email_en_uso(email, excluir_id=None):
    usuarios = Usuario.objects.filter(email__iexact=email)
    if excluir_id:
        usuarios = usuarios.exclude(pk=excluir_id)
    return usuarios.exists()


def crear(**datos):
    return Usuario.objects.create(**datos)


def actualizar(id_usuario, **datos):
    Usuario.objects.filter(pk=id_usuario).update(**datos)


def mapa_por_id():
    return {u.id_usuario: u for u in Usuario.objects.all()}


# --- Roles ---

def listar_roles():
    return Rol.objects.order_by("id_rol")


def rol_por_nombre(nombre):
    return Rol.objects.filter(nombre__iexact=nombre).first()


def mapa_roles():
    return {r.id_rol: r for r in Rol.objects.all()}
