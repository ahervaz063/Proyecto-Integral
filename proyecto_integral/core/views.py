# core/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView as AuthLoginView
from core.models import Comision, Usuario, ComisionGuardada, Perfil, SolicitudEncargo, Resena
from core.forms import ComisionForm, RegistroForm, SolicitudEncargoForm, ResenaForm
from django.db.models import Avg, Count
from core.mixins import ClientRequiredMixin, ArtistRequiredMixin

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

            # Solicitudes recibidas
            context['solicitudes_recibidas'] = SolicitudEncargo.objects.filter(
                comision__artista=user
            ).select_related('cliente', 'comision').order_by('-fecha_solicitud')

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


# COMISIONES
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
class SolicitudCreateView(ClientRequiredMixin, LoginRequiredMixin, CreateView):
    model = SolicitudEncargo
    form_class = SolicitudEncargoForm
    template_name = 'core/solicitudes/form.html'

    def dispatch(self, request, *args, **kwargs):
        self.comision = get_object_or_404(Comision, id=self.kwargs['comision_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.cliente = self.request.user
        form.instance.comision = self.comision
        messages.success(self.request, "Solicitud enviada correctamente. El artista te responderá pronto.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comision'] = self.comision
        return context

    def get_success_url(self):
        return reverse_lazy('mis_solicitudes_cliente')


class SolicitudesArtistaListView(ArtistRequiredMixin, LoginRequiredMixin, ListView):
    model = SolicitudEncargo
    template_name = 'core/solicitudes/artista_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 10

    def get_queryset(self):
        return SolicitudEncargo.objects.filter(
            comision__artista=self.request.user
        ).select_related('cliente', 'comision').order_by('-fecha_solicitud')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Contar solicitudes pendientes
        context['solicitudes_pendientes'] = self.get_queryset().filter(estado='pendiente').count()
        return context


class SolicitudesClienteListView(ClientRequiredMixin, LoginRequiredMixin, ListView):
    model = SolicitudEncargo
    template_name = 'core/solicitudes/cliente_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 10

    def get_queryset(self):
        return SolicitudEncargo.objects.filter(
            cliente=self.request.user
        ).select_related('comision__artista').order_by('-fecha_solicitud')


def aceptar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudEncargo, id=solicitud_id)

    # Verificar que el usuario es el artista dueño de la comisión o admin
    if request.user != solicitud.comision.artista and not request.user.is_staff:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('solicitudes_artista')

    if solicitud.aceptar():
        messages.success(request, f"Solicitud de {solicitud.cliente.username} aceptada. Slot ocupado.")
    else:
        messages.error(request, "No hay slots disponibles para esta comisión.")

    return redirect('solicitudes_artista')



def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudEncargo, id=solicitud_id)

    if request.user != solicitud.comision.artista and not request.user.is_staff:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('solicitudes_artista')

    solicitud.rechazar()
    messages.success(request, f"Solicitud de {solicitud.cliente.username} rechazada.")
    return redirect('solicitudes_artista')


def cancelar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudEncargo, id=solicitud_id)

    if request.user != solicitud.cliente and not request.user.is_staff:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('mis_solicitudes_cliente')

    if solicitud.cancelar():
        messages.success(request, "Solicitud cancelada correctamente.")
    else:
        messages.error(request, "Solo puedes cancelar solicitudes pendientes.")

    return redirect('mis_solicitudes_cliente')


def finalizar_encargo(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudEncargo, id=solicitud_id)

    if request.user != solicitud.comision.artista and not request.user.is_staff:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('solicitudes_artista')

    if solicitud.finalizar():
        messages.success(request, "Encargo finalizado. Espera la reseña del cliente.")
    else:
        messages.error(request, "Solo puedes finalizar encargos aceptados.")

    return redirect('solicitudes_artista')

#RESEÑAS
class ResenaCreateView(LoginRequiredMixin, CreateView):
    model = Resena
    form_class = ResenaForm
    template_name = 'core/resenas/form.html'

    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(SolicitudEncargo, id=self.kwargs['solicitud_id'])
        # Verificar que la solicitud está finalizada
        if self.solicitud.estado != 'finalizada':
            messages.error(request, "Solo puedes dejar reseña en encargos finalizados.")
            return redirect('mis_solicitudes_cliente')
        # Verificar que el usuario es el cliente de la solicitud
        if self.solicitud.cliente != request.user:
            messages.error(request, "No tienes permiso para reseñar este encargo.")
            return redirect('mis_solicitudes_cliente')
        # Verificar que no existe ya una reseña
        if hasattr(self.solicitud, 'reseña'):
            messages.error(request, "Ya has dejado una reseña para este encargo.")
            return redirect('mis_solicitudes_cliente')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.cliente = self.request.user
        form.instance.artista = self.solicitud.comision.artista
        form.instance.solicitud = self.solicitud
        messages.success(self.request, "¡Gracias por tu reseña! Ayuda a otros usuarios.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('mis_solicitudes_cliente')