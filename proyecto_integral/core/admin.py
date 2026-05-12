from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.models import Usuario, Perfil, Comision, Politica, PortfolioImagen, SolicitudEncargo, Resena, ComisionGuardada

# Registro del modelo Usuario personalizado
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'tipo_usuario', 'is_staff', 'is_active')
    list_filter = ('tipo_usuario', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('tipo_usuario', 'fecha_nacimiento')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('email', 'tipo_usuario', 'fecha_nacimiento')}),
    )

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Perfil)
admin.site.register(Comision)
admin.site.register(Politica)
admin.site.register(PortfolioImagen)
admin.site.register(SolicitudEncargo)
admin.site.register(Resena)
admin.site.register(ComisionGuardada)