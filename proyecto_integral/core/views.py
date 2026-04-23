# core/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView as AuthLoginView
from core.models import Comision, Usuario, ComisionGuardada, Perfil
from core.forms import ComisionForm, RegistroForm
from django.db.models import Avg, Count

from django.contrib.auth.mixins import LoginRequiredMixin

# VISTAS PÚBLICAS
class HomeView(TemplateView):
    template_name = 'core/home.html'


class BuscarArtistasView(TemplateView):
    template_name = 'core/buscar.html'



# AUTENTICACIÓN (mínimo para arrancar)
class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = 'core/registro.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f"¡Bienvenido {self.object.username}!")
        return response


class LoginView(AuthLoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.es_artista():
            return reverse_lazy('perfil_artista', kwargs={'pk': user.pk})
        else:
            return reverse_lazy('perfil_cliente', kwargs={'pk': user.pk})


def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('home')


# PERFILES
class PerfilArtistaView(TemplateView):
    template_name = 'core/perfiles/artista.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.es_artista():
            reseñas = user.reseñas_recibidas.all()
            context['reseñas'] = reseñas
            context['total_reseñas'] = reseñas.count()
            context['media_puntuacion'] = reseñas.aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
        return context


class PerfilClienteView(TemplateView):
    template_name = 'core/perfiles/cliente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.es_cliente():
            # Solicitudes del cliente
            solicitudes = user.solicitudes_realizadas.all()
            context['solicitudes'] = solicitudes

            # Comisiones guardadas (favoritas)
            comisiones_guardadas = ComisionGuardada.objects.filter(cliente=user).select_related('comision',
                                                                                                'comision__artista')
            context['comisiones_guardadas'] = comisiones_guardadas

            # Reseñas escritas por el cliente
            reseñas = user.reseñas_escritas.all()
            context['reseñas'] = reseñas
            context['total_reseñas'] = reseñas.count()
            context['media_puntuacion'] = reseñas.aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
        return context


class EditarPerfilView(TemplateView):
    model = Usuario
    fields = ['first_name', 'last_name', 'username', 'email']
    template_name = 'core/perfiles/editar_form.html'
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadir el perfil al contexto para poder editar sus campos
        if hasattr(self.request.user, 'perfil'):
            context['perfil'] = self.request.user.perfil
        return context

    def form_valid(self, form):
        # Guardar el usuario
        response = super().form_valid(form)

        # Guardar los campos del perfil
        perfil = self.request.user.perfil
        perfil.descripcion = self.request.POST.get('descripcion', '')

        # Procesar redes sociales (JSON)
        redes_sociales = {}
        instagram = self.request.POST.get('instagram', '')
        twitter = self.request.POST.get('twitter', '')
        behance = self.request.POST.get('behance', '')

        if instagram:
            redes_sociales['instagram'] = instagram
        if twitter:
            redes_sociales['twitter'] = twitter
        if behance:
            redes_sociales['behance'] = behance

        perfil.redes_sociales = redes_sociales

        # Procesar foto de perfil
        if 'foto' in self.request.FILES:
            perfil.foto = self.request.FILES['foto']

        perfil.save()

        messages.success(self.request, "Perfil actualizado correctamente.")
        return response

    def get_success_url(self):
        # Redirigir al perfil correspondiente según el tipo de usuario
        if self.request.user.es_artista():
            return reverse_lazy('perfil_artista', kwargs={'pk': self.request.user.pk})
        else:
            return reverse_lazy('perfil_cliente', kwargs={'pk': self.request.user.pk})


# CRUD DE COMISIONES
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


# POLÍTICAS
class PoliticaCreateView(TemplateView):
    template_name = 'core/politicas/form.html'


class PoliticaUpdateView(TemplateView):
    template_name = 'core/politicas/form.html'


class PoliticaDeleteView(TemplateView):
    template_name = 'core/politicas/confirm_delete.html'


# PORTFOLIO
class PortfolioCreateView(TemplateView):
    template_name = 'core/portfolio/form.html'


class PortfolioDeleteView(TemplateView):
    template_name = 'core/portfolio/confirm_delete.html'


# SOLICITUDES DE ENCARGO
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