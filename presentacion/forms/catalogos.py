import re

from django import forms

from datos.models import CategoriaProducto, Marca, Proveedor


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = CategoriaProducto
        fields = ["nombre", "descripcion"]
        labels = {"descripcion": "Descripción"}


class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre"]


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nit", "nombre", "contacto", "telefono", "email", "direccion"]
        labels = {
            "nit": "NIT",
            "telefono": "Teléfono",
            "email": "Correo",
            "direccion": "Dirección",
        }
        widgets = {
            "email": forms.EmailInput(),
            "direccion": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_nit(self):
        nit = self.cleaned_data["nit"].strip().upper()
        if not nit:
            raise forms.ValidationError("El NIT es obligatorio.")
        return nit

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        return nombre

    def clean_telefono(self):
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if telefono and not re.fullmatch(r"[0-9+\-\s()]{7,20}", telefono):
            raise forms.ValidationError("Revise el número de teléfono.")
        return telefono or None

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip() or None
