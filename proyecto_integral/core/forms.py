# core/forms.py
from django import forms
from .models import Comision


class ComisionForm(forms.ModelForm):
    class Meta:
        model = Comision
        fields = ['nombre', 'precio', 'slots', 'tiempo_estimado', 'descripcion', 'imagen', 'politica',
                  'usos_permitidos']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor que 0.")
        return precio

    def clean_slots(self):
        slots = self.cleaned_data.get('slots')
        if slots < 1:
            raise forms.ValidationError("Debe haber al menos 1 slot disponible.")
        return slots