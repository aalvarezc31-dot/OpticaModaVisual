from django import forms

from datos.models import Producto
from negocio.servicios import productos


def _opciones(registros, campo_id, vacio):
    return [("", vacio)] + [
        (getattr(r, campo_id), r.nombre) for r in registros
    ]


class ProductoForm(forms.ModelForm):
    id_categoria = forms.TypedChoiceField(label="Categoría", coerce=int)
    id_marca = forms.TypedChoiceField(
        label="Marca", coerce=int, required=False, empty_value=None
    )
    id_proveedor = forms.TypedChoiceField(
        label="Proveedor", coerce=int, required=False, empty_value=None
    )
    stock_inicial = forms.IntegerField(
        label="Stock inicial", min_value=0, initial=0, required=False,
        help_text="Se registra como movimiento de ENTRADA.",
    )

    class Meta:
        model = Producto
        fields = [
            "codigo",
            "nombre",
            "id_categoria",
            "id_marca",
            "id_proveedor",
            "modelo",
            "color",
            "material",
            "descripcion",
            "es_servicio",
            "precio_costo",
            "precio_venta",
            "stock_minimo",
        ]
        labels = {
            "codigo": "Código",
            "es_servicio": "Es un servicio (no maneja stock)",
            "precio_costo": "Precio de costo (Q)",
            "precio_venta": "Precio de venta (Q)",
            "stock_minimo": "Stock mínimo",
            "descripcion": "Descripción",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "precio_costo": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "precio_venta": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "stock_minimo": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, nuevo=True, **kwargs):
        super().__init__(*args, **kwargs)
        catalogo = productos.opciones_catalogo()

        self.fields["id_categoria"].choices = _opciones(
            catalogo["categorias"], "id_categoria", "Selecciona una categoría"
        )
        self.fields["id_marca"].choices = _opciones(
            catalogo["marcas"], "id_marca", "Sin marca"
        )
        self.fields["id_proveedor"].choices = _opciones(
            catalogo["proveedores"], "id_proveedor", "Sin proveedor"
        )

        if not nuevo:
            # Al editar, el stock solo cambia con movimientos de inventario.
            del self.fields["stock_inicial"]

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip().upper()
        if not codigo:
            raise forms.ValidationError("Ingrese el código del producto.")
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if not nombre:
            raise forms.ValidationError("Ingrese el nombre del producto.")
        return nombre

    def clean(self):
        datos = super().clean()
        costo = datos.get("precio_costo")
        venta = datos.get("precio_venta")
        minimo = datos.get("stock_minimo")

        if costo is not None and costo < 0:
            self.add_error("precio_costo", "El costo no puede ser negativo.")

        if venta is not None and venta < 0:
            self.add_error("precio_venta", "El precio de venta no puede ser negativo.")

        if minimo is not None and minimo < 0:
            self.add_error("stock_minimo", "El stock mínimo no puede ser negativo.")

        return datos


class MovimientoForm(forms.Form):
    tipo = forms.ChoiceField(label="Tipo de movimiento", choices=productos.TIPOS_MOVIMIENTO)
    cantidad = forms.IntegerField(
        label="Cantidad",
        help_text="En un ajuste usa un número negativo para restar.",
    )
    id_proveedor = forms.TypedChoiceField(
        label="Proveedor (solo entradas)", coerce=int, required=False, empty_value=None
    )
    costo_unitario = forms.DecimalField(
        label="Costo unitario (Q)", max_digits=12, decimal_places=2,
        min_value=0, required=False,
    )
    motivo = forms.CharField(label="Motivo / referencia", max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_proveedor"].choices = _opciones(
            productos.opciones_catalogo()["proveedores"], "id_proveedor", "Sin proveedor"
        )
