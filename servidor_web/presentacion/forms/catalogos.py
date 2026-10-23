import re

from django import forms


class CategoriaForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=50)
    descripcion = forms.CharField(label="Descripción", max_length=150, required=False)

    def clean_descripcion(self):
        return (self.cleaned_data.get("descripcion") or "").strip() or None


class MarcaForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=60)


class ProveedorForm(forms.Form):
    nit = forms.CharField(label="NIT", max_length=15)
    nombre = forms.CharField(label="Nombre", max_length=120)
    contacto = forms.CharField(label="Contacto", max_length=100, required=False)
    telefono = forms.CharField(label="Teléfono", max_length=20, required=False)
    email = forms.EmailField(label="Correo", max_length=120, required=False)
    direccion = forms.CharField(
        label="Dirección", max_length=200, required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

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

    def clean_contacto(self):
        return (self.cleaned_data.get("contacto") or "").strip() or None

    def clean_telefono(self):
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if telefono and not re.fullmatch(r"[0-9+\-\s()]{7,20}", telefono):
            raise forms.ValidationError("Revise el número de teléfono.")
        return telefono or None

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip() or None

    def clean_direccion(self):
        return (self.cleaned_data.get("direccion") or "").strip() or None
