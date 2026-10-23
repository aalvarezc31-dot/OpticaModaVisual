import re
from datetime import date

from django import forms


class ClienteForm(forms.Form):
    # Los largos máximos son los de la tabla clientes.cliente.
    dpi = forms.CharField(label="DPI", max_length=13, required=False)
    nit = forms.CharField(label="NIT", max_length=15, initial="CF")
    nombres = forms.CharField(label="Nombres", max_length=80)
    apellidos = forms.CharField(label="Apellidos", max_length=80)
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    genero = forms.ChoiceField(
        label="Género", required=False,
        choices=[("", "Seleccione"), ("M", "Masculino"), ("F", "Femenino"), ("O", "Otro")],
    )
    telefono = forms.CharField(label="Teléfono", max_length=20, required=False)
    email = forms.EmailField(label="Correo", max_length=120, required=False)
    direccion = forms.CharField(
        label="Dirección", max_length=200, required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_nombres(self):
        nombres = self.cleaned_data["nombres"].strip()
        if not nombres:
            raise forms.ValidationError("Ingrese los nombres del cliente.")
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data["apellidos"].strip()
        if not apellidos:
            raise forms.ValidationError("Ingrese los apellidos del cliente.")
        return apellidos

    def clean_nit(self):
        nit = (self.cleaned_data.get("nit") or "").strip().upper()
        if not nit:
            raise forms.ValidationError("El NIT es obligatorio.")
        return nit

    def clean_dpi(self):
        dpi = (self.cleaned_data.get("dpi") or "").strip()
        if dpi and not re.fullmatch(r"\d{13}", dpi):
            raise forms.ValidationError(
                "El DPI debe contener exactamente 13 dígitos."
            )
        return dpi or None

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get("fecha_nacimiento")
        if fecha and fecha > date.today():
            raise forms.ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )
        return fecha

    def clean_genero(self):
        return self.cleaned_data.get("genero") or None

    def clean_telefono(self):
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if telefono and not re.fullmatch(r"[0-9+\-\s()]{7,20}", telefono):
            raise forms.ValidationError("Revise el número de teléfono.")
        return telefono or None

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        return email or None

    def clean_direccion(self):
        return (self.cleaned_data.get("direccion") or "").strip() or None
