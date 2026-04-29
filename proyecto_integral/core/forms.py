# core/forms.py
from django import forms
from .models import Comision, Usuario, SolicitudEncargo, Resena
from django.contrib.auth.forms import UserCreationForm

class ComisionForm(forms.ModelForm):
    categorias_seleccionadas = forms.MultipleChoiceField(
        choices=Comision.CATEGORIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Categorías (máximo 3)"
    )

    class Meta:
        model = Comision
        fields = ['nombre', 'precio', 'slots', 'tiempo_estimado', 'descripcion', 'imagen', 'politica',
                  'usos_permitidos', 'categorias']
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

    def clean_categorias_seleccionadas(self):
        categorias = self.cleaned_data.get('categorias_seleccionadas', [])
        if len(categorias) > 3:
            raise forms.ValidationError("Máximo 3 categorías por comisión.")
        return categorias

    def save(self, commit=True):
        comision = super().save(commit=False)
        if commit:
            comision.save()
            # Guardar categorías como string separado por comas
            categorias = self.cleaned_data.get('categorias_seleccionadas', [])
            comision.categorias = ','.join(categorias)
            comision.save()
        return comision


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")
    first_name = forms.CharField(required=True, label="Nombre")
    last_name = forms.CharField(required=True, label="Apellidos")
    fecha_nacimiento = forms.DateField(
        required=False,
        label="Fecha de nacimiento",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    tipo_usuario = forms.ChoiceField(
        choices=Usuario.TIPO_USUARIO,
        widget=forms.HiddenInput(),  # Oculto, lo controlamos con JavaScript
        initial='cliente'
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'fecha_nacimiento', 'tipo_usuario', 'password1',
                  'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.tipo_usuario = self.cleaned_data['tipo_usuario']
        if commit:
            user.save()
        return user


class SolicitudEncargoForm(forms.ModelForm):
    class Meta:
        model = SolicitudEncargo
        fields = ['email', 'instagram', 'descripcion_idea', 'referencias']
        widgets = {
            'descripcion_idea': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Describe detalladamente tu idea...'}
            ),
            'email': forms.EmailInput(attrs={'placeholder': 'tu@email.com'}),
            'instagram': forms.TextInput(attrs={'placeholder': '@usuario'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        return email



class ResenaForm(forms.ModelForm):
    class Meta:
        model = Resena
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.Select(choices=[(i, f"{i} estrellas") for i in range(1, 6)]),
            'comentario': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Cuéntanos tu experiencia con el artista...'}),
        }