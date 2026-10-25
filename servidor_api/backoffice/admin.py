"""
Panel administrativo de Django (/admin/).

- Roles y Usuarios del sistema (seguridad.rol / seguridad.usuario): el rol se
  cambia directamente desde la lista.
- Usuarios de Django (cuentas de login): muestran su rol y, al guardarlos, se
  crea o actualiza su usuario del sistema con el mismo username.
"""
from django import forms
from django.db import IntegrityError, models
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone

from datos.models import (
    CategoriaProducto, Marca, MovimientoInventario, Producto, Proveedor, Rol, Usuario,
)
from negocio.excepciones import ReglaNegocioError
from negocio.servicios import productos as servicio_productos
from negocio.servicios import usuarios as servicio_usuarios

admin.site.site_header = "Óptica Moda Visual · Administración"
admin.site.site_title = "Óptica Moda Visual"
admin.site.index_title = "Panel administrativo"


# El rol se guarda como VENDEDOR en la base; en el sistema se llama "Agente".
NOMBRE_VISIBLE_ROL = {"VENDEDOR": "AGENTE"}


def nombre_rol(nombre):
    return NOMBRE_VISIBLE_ROL.get((nombre or "").upper(), nombre)


def _opciones_rol():
    return [(r.id_rol, nombre_rol(r.nombre)) for r in Rol.objects.order_by("nombre")]


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ["nombre_visible", "descripcion", "cantidad_usuarios"]

    @admin.display(description="Rol", ordering="nombre")
    def nombre_visible(self, rol):
        return nombre_rol(rol.nombre)
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

    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super().add_view(request, form_url, extra_context)
        except IntegrityError:
            # Dos envíos casi simultáneos del mismo formulario: el primero ya lo creó.
            self.message_user(
                request,
                "Ese nombre de usuario ya existe (el formulario se envió dos veces). "
                "Búscalo en la lista para editarlo.",
                messages.WARNING,
            )
            return redirect("admin:auth_user_changelist")

    @admin.display(description="Rol en el sistema")
    def rol_sistema(self, cuenta):
        rol = servicio_usuarios.rol_de_cuenta(cuenta)
        return nombre_rol(rol) if rol else "— sin usuario del sistema —"

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


# --- Inventario: productos con existencias editables ---

def _opciones(modelo, campo_id, vacio=None):
    opciones = [(getattr(r, campo_id), r.nombre) for r in modelo.objects.order_by("nombre")]
    return ([("", vacio)] if vacio else []) + opciones


class ProductoAdminForm(forms.ModelForm):
    stock_nuevo = forms.IntegerField(
        label="Nuevas existencias", min_value=0, required=False,
        help_text="Escribe la cantidad real que hay en tienda. Se registra un "
                  "movimiento de AJUSTE por la diferencia. Déjalo vacío para no cambiarlo.",
    )
    motivo_ajuste = forms.CharField(
        label="Motivo del ajuste", max_length=200, required=False,
        help_text="Ej.: conteo físico, producto dañado, corrección.",
    )

    class Meta:
        model = Producto
        exclude = ["stock_actual", "fecha_creacion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_categoria"] = forms.TypedChoiceField(
            label="Categoría", coerce=int,
            choices=_opciones(CategoriaProducto, "id_categoria", "Selecciona"),
        )
        self.fields["id_marca"] = forms.TypedChoiceField(
            label="Marca", coerce=int, required=False, empty_value=None,
            choices=_opciones(Marca, "id_marca", "Sin marca"),
        )
        self.fields["id_proveedor"] = forms.TypedChoiceField(
            label="Proveedor", coerce=int, required=False, empty_value=None,
            choices=_opciones(Proveedor, "id_proveedor", "Sin proveedor"),
        )

    def clean(self):
        datos = super().clean()
        if self.errors:
            return datos

        if datos.get("es_servicio") and datos.get("stock_nuevo"):
            self.add_error("stock_nuevo", "Los servicios no manejan existencias.")

        try:
            servicio_productos.validar(
                {**datos, "codigo": datos["codigo"].strip().upper()},
                excluir_id=self.instance.pk,
            )
        except ReglaNegocioError as error:
            self.add_error(error.campo if error.campo in self.fields else None, error.mensaje)

        datos["codigo"] = datos["codigo"].strip().upper()
        return datos


class CategoriaFiltro(admin.SimpleListFilter):
    title = "categoría"
    parameter_name = "categoria"

    def lookups(self, request, model_admin):
        return [(c.id_categoria, c.nombre) for c in CategoriaProducto.objects.order_by("nombre")]

    def queryset(self, request, queryset):
        return queryset.filter(id_categoria=self.value()) if self.value() else queryset


class StockBajoFiltro(admin.SimpleListFilter):
    title = "existencias"
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        return [("bajo", "Stock bajo"), ("agotado", "Agotado")]

    def queryset(self, request, queryset):
        productos = queryset.filter(es_servicio=False)
        if self.value() == "bajo":
            return productos.filter(stock_actual__lte=models.F("stock_minimo"))
        if self.value() == "agotado":
            return productos.filter(stock_actual=0)
        return queryset


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoAdminForm
    list_display = [
        "codigo", "nombre", "categoria", "marca", "precio_venta",
        "stock_actual", "stock_minimo", "estado_stock", "activo",
    ]
    list_display_links = ["codigo", "nombre"]
    list_filter = [CategoriaFiltro, StockBajoFiltro, "es_servicio", "activo"]
    search_fields = ["codigo", "nombre", "modelo", "color"]
    ordering = ["nombre"]
    readonly_fields = ["stock_actual", "fecha_creacion"]
    fieldsets = [
        ("Producto", {"fields": ["codigo", "nombre", "id_categoria", "id_marca",
                                 "id_proveedor", "modelo", "color", "material",
                                 "descripcion", "es_servicio", "activo"]}),
        ("Precios", {"fields": ["precio_costo", "precio_venta"]}),
        ("Existencias", {"fields": ["stock_actual", "stock_minimo", "stock_nuevo",
                                    "motivo_ajuste", "fecha_creacion"]}),
    ]

    @admin.display(description="Categoría")
    def categoria(self, producto):
        categoria = CategoriaProducto.objects.filter(pk=producto.id_categoria).first()
        return categoria.nombre if categoria else "—"

    @admin.display(description="Marca")
    def marca(self, producto):
        marca = Marca.objects.filter(pk=producto.id_marca).first() if producto.id_marca else None
        return marca.nombre if marca else "—"

    @admin.display(description="Estado")
    def estado_stock(self, producto):
        if producto.es_servicio:
            return "Servicio"
        if producto.stock_actual == 0:
            return "Agotado"
        if producto.stock_actual <= producto.stock_minimo:
            return "Stock bajo"
        return "Disponible"

    def save_model(self, request, obj, form, change):
        campos = [f.name for f in Producto._meta.concrete_fields
                  if f.name in form.cleaned_data]

        if change:
            # Nunca se escribe stock_actual directamente: lo mantiene el trigger.
            obj.save(update_fields=campos)
        else:
            obj.stock_actual = 0
            obj.fecha_creacion = timezone.now()
            obj.save(force_insert=True)

        try:
            diferencia = servicio_productos.ajustar_stock(
                request.user, obj.pk,
                form.cleaned_data.get("stock_nuevo"),
                form.cleaned_data.get("motivo_ajuste"),
            )
        except ReglaNegocioError as error:
            self.message_user(request, f"Producto guardado, pero el stock no cambió: {error.mensaje}",
                              messages.ERROR)
            return

        if diferencia:
            obj.refresh_from_db()
            self.message_user(
                request,
                f"Existencias ajustadas en {diferencia:+d}. Ahora hay {obj.stock_actual}.",
                messages.SUCCESS,
            )

    def has_delete_permission(self, request, obj=None):
        # Los productos tienen ventas y movimientos: se desactivan, no se borran.
        return False


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    """Historial de entradas, salidas y ajustes (solo lectura)."""
    list_display = ["fecha", "producto", "tipo", "cantidad", "motivo", "venta", "usuario"]
    list_filter = ["tipo"]
    search_fields = ["motivo"]
    date_hierarchy = "fecha"
    ordering = ["-fecha", "-id_movimiento"]

    @admin.display(description="Producto")
    def producto(self, movimiento):
        producto = Producto.objects.filter(pk=movimiento.id_producto).first()
        return str(producto) if producto else movimiento.id_producto

    @admin.display(description="Venta")
    def venta(self, movimiento):
        return f"#{movimiento.id_venta}" if movimiento.id_venta else "—"

    @admin.display(description="Usuario")
    def usuario(self, movimiento):
        usuario = Usuario.objects.filter(pk=movimiento.id_usuario).first()
        return usuario.username if usuario else movimiento.id_usuario

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
