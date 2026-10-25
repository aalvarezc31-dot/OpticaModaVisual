import json
from decimal import Decimal, InvalidOperation

from django import forms

from presentacion import validaciones
from presentacion.servicios import ventas


class NuevaVentaForm(forms.Form):
    """
    Paso 2 de la venta: los datos de la compra. El carrito del paso 1 llega
    en `lineas` como JSON (lo arma la página con JavaScript).
    """
    lineas = forms.CharField(widget=forms.HiddenInput, required=False)
    id_cliente = forms.TypedChoiceField(
        label="Cliente", coerce=int,
        widget=forms.Select(attrs={"data-buscable": "Buscar cliente por nombre o NIT…"}),
    )
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
    descuento = forms.DecimalField(
        label="Descuento general (Q)", max_digits=12, decimal_places=2, min_value=0,
        required=False, initial=Decimal("0"),
    )
    confirmar = forms.BooleanField(
        label="Confirmar la venta al crearla (descuenta el inventario)", required=False, initial=True,
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


    def clean_descuento(self):
        return self.cleaned_data.get("descuento") or Decimal("0")

    def clean_lineas(self):
        """Valida el carrito: [{id_producto, cantidad, descuento, precio_unitario}, ...]."""
        try:
            crudas = json.loads(self.cleaned_data.get("lineas") or "[]")
        except ValueError:
            raise forms.ValidationError("El carrito no es válido. Vuelve a agregar los productos.")

        if not isinstance(crudas, list) or not crudas:
            raise forms.ValidationError("Paso 1: agrega al menos un producto o servicio al carrito.")

        lineas = []
        try:
            for cruda in crudas:
                linea = {
                    "id_producto": int(cruda["id_producto"]),
                    "cantidad": int(cruda["cantidad"]),
                    "descuento": Decimal(str(cruda.get("descuento") or "0")),
                    "precio_unitario": (Decimal(str(cruda["precio_unitario"]))
                                        if cruda.get("precio_unitario") not in (None, "") else None),
                }
                if linea["cantidad"] < 1 or linea["descuento"] < 0 or (
                        linea["precio_unitario"] is not None and linea["precio_unitario"] < 0):
                    raise ValueError
                lineas.append(linea)
        except (KeyError, TypeError, ValueError, InvalidOperation):
            raise forms.ValidationError("Hay una línea del carrito con datos inválidos.")
        return lineas


class LineaVentaForm(forms.Form):
    id_producto = forms.TypedChoiceField(
        label="Producto", coerce=int,
        widget=forms.Select(attrs={"data-buscable": "Buscar por código o nombre…"}),
    )
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
        disponibles = ventas.productos_para_venta()
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
        label="Referencia del voucher (solo números)", max_length=60, required=False,
        widget=forms.TextInput(attrs=validaciones.ATTRS_VOUCHER),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_metodo_pago"].choices = [("", "Selecciona")] + [
            (m.id_metodo_pago, m.nombre.capitalize()) for m in ventas.metodos_de_pago()
        ]

    def clean_referencia(self):
        return validaciones.limpiar_voucher(self.cleaned_data.get("referencia"))


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
