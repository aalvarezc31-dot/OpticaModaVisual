from django import forms


class RecetaOpticaForm(forms.Form):
    od_esfera = forms.DecimalField(
        label="OD - Esfera", max_digits=5, decimal_places=2,
        required=False
    )
    od_cilindro = forms.DecimalField(
        label="OD - Cilindro", max_digits=5, decimal_places=2,
        required=False
    )
    od_eje = forms.IntegerField(
        label="OD - Eje", required=False, min_value=0, max_value=180
    )
    od_adicion = forms.DecimalField(
        label="OD - Adición", max_digits=4, decimal_places=2,
        required=False
    )
    oi_esfera = forms.DecimalField(
        label="OI - Esfera", max_digits=5, decimal_places=2,
        required=False
    )
    oi_cilindro = forms.DecimalField(
        label="OI - Cilindro", max_digits=5, decimal_places=2,
        required=False
    )
    oi_eje = forms.IntegerField(
        label="OI - Eje", required=False, min_value=0, max_value=180
    )
    oi_adicion = forms.DecimalField(
        label="OI - Adición", max_digits=4, decimal_places=2,
        required=False
    )
    distancia_pupilar = forms.DecimalField(
        label="Distancia pupilar (mm)", max_digits=4,
        decimal_places=1, required=False, min_value=0
    )
    tipo_lente = forms.CharField(
        label="Tipo de lente", max_length=50, required=False
    )
    tratamiento = forms.CharField(
        label="Tratamiento", max_length=100, required=False
    )
    indicaciones = forms.CharField(
        label="Indicaciones", required=False,
        widget=forms.Textarea(attrs={"rows": 3})
    )
    fecha_emision = forms.DateField(
        label="Fecha de emisión",
        widget=forms.DateInput(attrs={"type": "date"})
    )
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean(self):
        datos = super().clean()
        emision = datos.get("fecha_emision")
        vencimiento = datos.get("fecha_vencimiento")

        if emision and vencimiento and vencimiento < emision:
            self.add_error(
                "fecha_vencimiento",
                "La fecha de vencimiento no puede ser anterior a la emisión."
            )

        return datos
