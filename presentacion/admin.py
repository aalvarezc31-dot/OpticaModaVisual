"""
Panel administrativo de Django (/admin/).

- Roles y Usuarios del sistema (seguridad.rol / seguridad.usuario): el rol se
  cambia directamente desde la lista.
- Usuarios de Django (cuentas de login): muestran su rol y, al guardarlos, se
  crea o actualiza su usuario del sistema con el mismo username.
"""
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone

from datos.models import Rol, Usuario
from negocio.servicios import usuarios as servicio_usuarios

admin.site.site_header = "Óptica Moda Visual · Administración"
admin.site.site_title = "Óptica Moda Visual"
admin.site.index_title = "Panel administrativo"


def _opciones_rol():
    return [(r.id_rol, r.nombre) for r in Rol.objects.order_by("nombre")]


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion", "cantidad_usuarios"]
    search_fields = ["nombre"]
    ordering = ["id_rol"]

    @admin.display(description="Usuarios")
    def cantidad_usuarios(self, rol):
        return Usuario.objects.filter(id_rol=rol.id_rol).count()


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    change_list_template = "admin/datos/usuario/change_list.html"
    list_display = [
        "username", "nombre_completo", "id_rol", "activo", "email",
        "cuenta_django", "ultimo_acceso",
    ]
    # El rol y el estado se cambian directamente en la lista (botón Guardar abajo).
    list_editable = ["id_rol", "activo"]
    list_filter = ["activo", "id_rol"]
    search_fields = ["username", "nombres", "apellidos", "email"]
    readonly_fields = ["ultimo_acceso", "fecha_creacion", "cuenta_django"]
    # password_hash no se muestra: el login se hace con la cuenta de Django.
    fields = [
        "username", "nombres", "apellidos", "email", "telefono", "id_rol",
        "activo", "cuenta_django", "ultimo_acceso", "fecha_creacion",
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "id_rol":
            return forms.TypedChoiceField(label="Rol", coerce=int, choices=_opciones_rol())
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @admin.display(description="Nombre")
    def nombre_completo(self, usuario):
        return f"{usuario.nombres} {usuario.apellidos}".strip()

    @admin.display(description="Cuenta de login", boolean=True)
    def cuenta_django(self, usuario):
        """Las operaciones se registran a su nombre solo si existe esta cuenta."""
        if not usuario.pk:
            return None
        return User.objects.filter(username__iexact=usuario.username).exists()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.fecha_creacion = timezone.now()
            obj.password_hash = make_password(None)  # sin contraseña propia
        super().save_model(request, obj, form, change)

    # --- Botón "Agregar cuentas de login que faltan" ---

    def get_urls(self):
        propias = [
            path(
                "importar-cuentas/",
                self.admin_site.admin_view(self.importar_cuentas),
                name="datos_usuario_importar_cuentas",
            ),
        ]
        return propias + super().get_urls()

    def importar_cuentas(self, request):
        if request.method != "POST":
            return redirect("admin:datos_usuario_changelist")

        creados = 0
        for cuenta in User.objects.order_by("username"):
            _, creado = servicio_usuarios.enlazar_cuenta(cuenta)
            creados += creado

        self.message_user(
            request,
            f"{creados} cuenta(s) de login agregadas como usuarios del sistema. "
            "Asígnales el rol en la lista y pulsa Guardar."
            if creados else "Todas las cuentas de login ya estaban en la lista.",
            messages.SUCCESS,
        )
        return redirect("admin:datos_usuario_changelist")


# --- Cuentas de login de Django con su rol ---

admin.site.unregister(User)


@admin.register(User)
class CuentaLoginAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "email", "rol_sistema",
                    "is_active", "is_staff", "is_superuser"]
    actions = ["enlazar_con_sistema"]

    @admin.display(description="Rol en el sistema")
    def rol_sistema(self, cuenta):
        return servicio_usuarios.rol_de_cuenta(cuenta) or "— sin usuario del sistema —"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _, creado = servicio_usuarios.enlazar_cuenta(obj)
        if creado:
            self.message_user(
                request,
                f"Se creó el usuario del sistema «{obj.username}». "
                "Asígnale su rol en «Usuarios del sistema (con rol)».",
                messages.INFO,
            )

    @admin.action(description="Agregar/actualizar como usuario del sistema (con rol)")
    def enlazar_con_sistema(self, request, queryset):
        creados = sum(servicio_usuarios.enlazar_cuenta(cuenta)[1] for cuenta in queryset)
        self.message_user(request, f"Listo. {creados} usuario(s) del sistema creados.")
