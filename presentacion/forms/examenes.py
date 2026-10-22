from django import forms

from negocio.servicios import citas, clientes, examenes


class ExamenVisualForm(forms.Form):
    # Los querysets se cargan en __init__ desde la capa de negocio.
    cliente = forms.ModelChoiceField(
        queryset=None,
        label="Paciente"
    )

    cita = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Cita relacionada",
        empty_label="Sin cita relacionada"
    )

    optometrista = forms.ModelChoiceField(
        queryset=None,
        label="Optometrista"
    )

    fecha_examen = forms.DateTimeField(
        label="Fecha y hora del examen",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"}
        )
    )

    motivo_consulta = forms.CharField(
        label="Motivo de consulta",
        max_length=255,
        required=False
    )

    antecedentes = forms.CharField(
        label="Antecedentes",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3})
    )

    agudeza_visual_od = forms.CharField(
        label="Agudeza visual OD (ojo derecho)",
        max_length=10,
        required=False
    )

    agudeza_visual_oi = forms.CharField(
        label="Agudeza visual OI (ojo izquierdo)",
        max_length=10,
        required=False
    )

    presion_intraocular_od = forms.DecimalField(
        label="Presión ocular OD",
        max_digits=4,
        decimal_places=1,
        required=False,
        min_value=0
    )

    presion_intraocular_oi = forms.DecimalField(
        label="Presión ocular OI",
        max_digits=4,
        decimal_places=1,
        required=False,
        min_value=0
    )

    diagnostico = forms.CharField(
        label="Diagnóstico",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3})
    )

    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cliente"].queryset = clientes.pacientes_activos()
        self.fields["cita"].queryset = citas.citas_para_examen()
        self.fields["optometrista"].queryset = (
            examenes.optometristas_activos()
        )

        # Mostrar nombres y apellidos de los pacientes.
        self.fields["cliente"].label_from_instance = (
            lambda obj: f"{obj.nombres} {obj.apellidos}"
        )

        # Mostrar nombres y apellidos de los optometristas.
        self.fields["optometrista"].label_from_instance = (
            lambda obj: f"{obj.nombres} {obj.apellidos}"
        )

        # Mostrar información identificable de cada cita.
        self.fields["cita"].label_from_instance = (
            lambda obj: f"Cita #{obj.pk} - {obj.fecha_hora_inicio}"
        )
