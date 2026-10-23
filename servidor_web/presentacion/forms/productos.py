from django import forms

from presentacion.servicios import productos


def _opciones(registros, campo_id, vacio):
    return [("", vacio)] + [(r[campo_id], r.nombre) for r in registros]


def _texto_opcional(valor):
    return (valor or "").strip() or None


class ProductoForm(forms.Form):
    # Los largos máximos son los de la tabla inventario.producto.
    codigo = forms.CharField(label="Código", max_length=30)
    nombre = forms.CharField(label="Nombre", max_length=120)
    id_categoria = forms.TypedChoiceField(label="Categoría", coerce=int)
    id_marca = forms.TypedChoiceField(
        label="Marca", coerce=int, required=False, empty_value=None
    )
    id_proveedor = forms.TypedChoiceField(
        label="Proveedor", coerce=int, required=False, empty_value=None
    )
    modelo = forms.CharField(label="Modelo", max_length=60, required=False)
    color = forms.CharField(label="Color", max_length=40, required=False)
    material = forms.CharField(label="Material", max_length=60, required=False)
    descripcion = forms.CharField(
        label="Descripción", max_length=255, required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    es_servicio = forms.BooleanField(label="Es un servicio (no maneja stock)", required=False)
    precio_costo = forms.DecimalField(
        label="Precio de costo (Q)", max_digits=12, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )
    precio_venta = forms.DecimalField(
        label="Precio de venta (Q)", max_digits=12, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
    )
    stock_minimo = forms.IntegerField(
        label="Stock mínimo", min_value=0, initial=0,
        widget=forms.NumberInput(attrs={"min": "0"}),
    )
    stock_inicial = forms.IntegerField(
        label="Stock inicial", min_value=0, initial=0, required=False,
        help_text="Se registra como movimiento de ENTRADA.",
    )

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

    def clean_modelo(self):
        return _texto_opcional(self.cleaned_data.get("modelo"))

    def clean_color(self):
        return _texto_opcional(self.cleaned_data.get("color"))

    def clean_material(self):
        return _texto_opcional(self.cleaned_data.get("material"))

    def clean_descripcion(self):
        return _texto_opcional(self.cleaned_data.get("descripcion"))


class MovimientoForm(forms.Form):
    tipo = forms.ChoiceField(label="Tipo de movimiento")
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
        self.fields["tipo"].choices = productos.tipos_movimiento()
        self.fields["id_proveedor"].choices = _opciones(
            productos.opciones_catalogo()["proveedores"], "id_proveedor", "Sin proveedor"
        )
