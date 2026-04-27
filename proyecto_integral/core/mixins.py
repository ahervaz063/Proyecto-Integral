from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied


# Mixin para exigir que el usuario sea ARTISTA
class ArtistRequiredMixin(UserPassesTestMixin, LoginRequiredMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_artista()

    def handle_no_permission(self):
        raise PermissionDenied("Debes ser artista para acceder a esta página.")


# Mixin para exigir que el usuario sea CLIENTE
class ClientRequiredMixin(UserPassesTestMixin, LoginRequiredMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_cliente()

    def handle_no_permission(self):
        raise PermissionDenied("Debes ser cliente para acceder a esta página.")


# Mixin para exigir que el usuario sea ADMIN
class AdminRequiredMixin(UserPassesTestMixin, LoginRequiredMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_admin()

    def handle_no_permission(self):
        raise PermissionDenied("Acceso solo para administradores.")


# Mixin para verificar que el usuario es el dueño del objeto o admin
class OwnershipMixin:
    """
    Verifica que el usuario actual sea el dueño del objeto (artista/cliente)
    o un administrador.
    """

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Verificar si el objeto tiene un campo 'artista' o 'cliente'
        if hasattr(obj, 'artista') and obj.artista == request.user:
            return super().dispatch(request, *args, **kwargs)
        if hasattr(obj, 'cliente') and obj.cliente == request.user:
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.es_admin():
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied("No tienes permiso para modificar este recurso.")