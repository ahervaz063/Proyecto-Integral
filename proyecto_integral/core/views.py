# core/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from core.models import Comision, Usuario
from core.forms import ComisionForm

# ============================================
# VISTAS PÚBLICAS
# ============================================

class HomeView(TemplateView):
    template_name = 'core/home.html'


class BuscarArtistasView(TemplateView):
    template_name = 'core/buscar.html'


# ============================================
# AUTENTICACIÓN (mínimo para arrancar)
# ============================================

class RegistroView(TemplateView):
    template_name = 'core/registro.html'


class LoginView(TemplateView):
    template_name = 'core/login.html'


def logout_view(request):
    return redirect('home')


# ============================================
# PERFILES
# ============================================

class PerfilArtistaView(TemplateView):
    template_name = 'core/perfiles/artista.html'


class PerfilClienteView(TemplateView):
    template_name = 'core/perfiles/cliente.html'


class EditarPerfilView(TemplateView):
    template_name = 'core/perfiles/editar_form.html'


# ============================================
# CRUD DE COMISIONES
# ============================================

class ComisionListView(ListView):
    model = Comision
    template_name = 'core/comisiones/list.html'
    context_object_name = 'comisiones'
    paginate_by = 12

    def get_queryset(self):
        return Comision.objects.filter(
            artista_id=self.kwargs['artista_id'],
            activa=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['artista'] = get_object_or_404(Usuario, id=self.kwargs['artista_id'])
        return context


class ComisionDetailView(DetailView):
    model = Comision
    template_name = 'core/comisiones/detail.html'
    context_object_name = 'comision'


class ComisionCreateView(CreateView):
    model = Comision
    form_class = ComisionForm
    template_name = 'core/comisiones/form.html'

    def form_valid(self, form):
        form.instance.artista = self.request.user
        messages.success(self.request, "Comisión creada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('perfil_artista', kwargs={'artista_id': self.request.user.id})


class ComisionUpdateView(UpdateView):
    model = Comision
    form_class = ComisionForm
    template_name = 'core/comisiones/form.html'

    def form_valid(self, form):
        messages.success(self.request, "Comisión actualizada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('perfil_artista', kwargs={'artista_id': self.request.user.id})


class ComisionDeleteView(DeleteView):
    model = Comision
    template_name = 'core/comisiones/confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, "Comisión eliminada correctamente.")
        return reverse_lazy('perfil_artista', kwargs={'artista_id': self.request.user.id})


# ============================================
# POLÍTICAS
# ============================================

class PoliticaCreateView(TemplateView):
    template_name = 'core/politicas/form.html'


class PoliticaUpdateView(TemplateView):
    template_name = 'core/politicas/form.html'


class PoliticaDeleteView(TemplateView):
    template_name = 'core/politicas/confirm_delete.html'


# ============================================
# PORTFOLIO
# ============================================

class PortfolioCreateView(TemplateView):
    template_name = 'core/portfolio/form.html'


class PortfolioDeleteView(TemplateView):
    template_name = 'core/portfolio/confirm_delete.html'


# ============================================
# SOLICITUDES DE ENCARGO
# ============================================

class SolicitudCreateView(TemplateView):
    template_name = 'core/solicitudes/form.html'


class SolicitudesArtistaListView(TemplateView):
    template_name = 'core/solicitudes/artista_list.html'


class SolicitudesClienteListView(TemplateView):
    template_name = 'core/solicitudes/cliente_list.html'


def aceptar_solicitud(request, solicitud_id):
    return redirect('solicitudes_artista')


def rechazar_solicitud(request, solicitud_id):
    return redirect('solicitudes_artista')


def cancelar_solicitud(request, solicitud_id):
    return redirect('mis_solicitudes_cliente')