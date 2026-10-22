import re
from datetime import date

from django import forms

from datos.models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "dpi", "nit", "nombres", "apellidos",
            "fecha_nacimiento", "genero", "telefono",
            "email", "direccion",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "direccion": forms.Textarea(attrs={"rows": 3}),
            "genero": forms.Select(choices=[
                ("", "Seleccione"),
                ("M", "Masculino"),
                ("F", "Femenino"),
                ("O", "Otro"),
            ]),
        }

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
        if len(nit) > 15:
            raise forms.ValidationError("El NIT no puede superar 15 caracteres.")
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

    def clean_telefono(self):
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if telefono and not re.fullmatch(r"[0-9+\-\s()]{7,20}", telefono):
            raise forms.ValidationError("Revise el número de teléfono.")
        return telefono

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        return email or None
