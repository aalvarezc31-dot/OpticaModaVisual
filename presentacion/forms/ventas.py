from decimal import Decimal

from django import forms

from negocio.servicios import productos, ventas


class NuevaVentaForm(forms.Form):
    id_cliente = forms.TypedChoiceField(label="Cliente", coerce=int)
    id_receta = forms.TypedChoiceField(
        label="Receta óptica (opcional)", coerce=int, required=False, empty_value=None,
        help_text="Déjalo en «Sin receta» para cobrar consultas, lentes de sol, accesorios, etc.",
    )
    fecha_entrega_estimada = forms.DateField(
        label="Fecha estimada de entrega", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    observaciones = forms.CharField(
        label="Observaciones", max_length=200, required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opciones = ventas.opciones_nueva_venta()

        self.fields["id_cliente"].choices = [("", "Selecciona un cliente")] + [
            (c.id_cliente, f"{c.nombres} {c.apellidos} — NIT {c.nit}")
            for c in opciones["clientes"]
        ]
        self.fields["id_receta"].choices = [("", "Sin receta")] + [
            (
                r.id_receta,
                f"#{r.id_receta} · {c.nombres} {c.apellidos} · "
                f"{r.fecha_emision:%d/%m/%Y} · {r.tipo_lente or 'lente'}",
            )
            for r, c in opciones["recetas"]
        ]


class LineaVentaForm(forms.Form):
    id_producto = forms.TypedChoiceField(label="Producto", coerce=int)
    cantidad = forms.IntegerField(label="Cantidad", min_value=1, initial=1)
    precio_unitario = forms.DecimalField(
        label="Precio (Q)", max_digits=12, decimal_places=2,
        min_value=0, required=False,
        help_text="Solo servicios: vacío = precio de lista.",
    )
    descuento = forms.DecimalField(
        label="Descuento (Q)", max_digits=12, decimal_places=2,
        min_value=0, initial=Decimal("0"), required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disponibles = list(productos.disponibles_para_venta())
        self.fields["id_producto"].choices = [("", "Selecciona un producto o servicio")] + [
            (
                p.id_producto,
                f"{p.codigo} · {p.nombre} · Q {p.precio_venta:.2f}"
                + (" · servicio (precio editable)" if p.es_servicio
                   else f" · stock {p.stock_actual}"),
            )
            for p in disponibles
        ]
        # Para que la plantilla sepa qué opciones son servicios y su precio.
        self.servicios = {p.id_producto: p.precio_venta for p in disponibles if p.es_servicio}

    def clean_descuento(self):
        return self.cleaned_data.get("descuento") or Decimal("0")


class DescuentoVentaForm(forms.Form):
    descuento = forms.DecimalField(
        label="Descuento general (Q)", max_digits=12, decimal_places=2, min_value=0
    )


class PagoForm(forms.Form):
    id_metodo_pago = forms.TypedChoiceField(label="Método de pago", coerce=int)
    monto = forms.DecimalField(
        label="Monto (Q)", max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    referencia = forms.CharField(
        label="Referencia (boleta, autorización...)", max_length=60, required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_metodo_pago"].choices = [("", "Selecciona")] + [
            (m.id_metodo_pago, m.nombre.capitalize()) for m in ventas.metodos_de_pago()
        ]


class MotivoForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo", max_length=200,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class EmitirFacturaForm(forms.Form):
    nit_receptor = forms.CharField(label="NIT", max_length=15, initial="CF")
    nombre_receptor = forms.CharField(label="Nombre", max_length=160)
    direccion_receptor = forms.CharField(
        label="Dirección", max_length=200, required=False, initial="Ciudad"
    )
