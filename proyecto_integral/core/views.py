# core/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView,View
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView as AuthLoginView
from core.models import Comision, Usuario, ComisionGuardada, Perfil, SolicitudEncargo, Resena, PortfolioImagen, Politica
from core.forms import ComisionForm, RegistroForm, SolicitudEncargoForm, ResenaForm, PoliticaForm
from django.db.models import Avg, Count, Q
from core.mixins import ClientRequiredMixin, ArtistRequiredMixin

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

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
    """Vista AJAX para obtener datos de una comisión (para editar)"""

    def get(self, request, *args, **kwargs):
        comision = get_object_or_404(Comision, id=kwargs['pk'])

        return JsonResponse({
            'success': True,
            'comision': {
                'id': comision.id,
                'nombre': comision.nombre,
                'precio': str(comision.precio),
                'slots': comision.slots,
                'tiempo_estimado': comision.tiempo_estimado,
                'descripcion': comision.descripcion,
                'imagen_url': comision.imagen.url if comision.imagen else None,
                'politica_id': comision.politica.id if comision.politica else '',
                'usos_permitidos': comision.usos_permitidos,
                'categorias': comision.categorias.split(',') if comision.categorias else [],
            }
        })


class ComisionCreateView(ArtistRequiredMixin, View):
    """Vista AJAX para crear comisión"""

    def post(self, request, *args, **kwargs):
        print("===== DEBUG COMISION CREATE =====")
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)

        form = ComisionForm(request.POST, request.FILES)

        if form.is_valid():
            print("Formulario válido")
            comision = form.save(commit=False)
            comision.artista = request.user
            comision.save()

            # Guardar categorías
            categorias = request.POST.getlist('categorias_seleccionadas')
            print("Categorías seleccionadas:", categorias)

            if len(categorias) > 3:
                return JsonResponse({
                    'success': False,
                    'error': 'Máximo 3 categorías por comisión.'
                }, status=400)

            comision.categorias = ','.join(categorias)
            comision.save()

            return JsonResponse({
                'success': True,
                'message': 'Comisión creada correctamente.',
                'comision': {
                    'id': comision.id,
                    'nombre': comision.nombre,
                    'precio': str(comision.precio),
                    'slots_disponibles': comision.slots_disponibles,
                    'tiempo_estimado': comision.tiempo_estimado,
                    'descripcion': comision.descripcion[:100],
                    'imagen_url': comision.imagen.url if comision.imagen else None,
                }
            })
        else:
            print("Errores del formulario:", form.errors)
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


class ComisionUpdateView(ArtistRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        print("===== DEBUG COMISION UPDATE =====")
        print("Comision ID:", kwargs.get('pk'))
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)

        comision = get_object_or_404(Comision, id=kwargs['pk'])

        # Verificar permisos
        if comision.artista != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'No tienes permiso para editar esta comisión.'}, status=403)

        form = ComisionForm(request.POST, request.FILES, instance=comision)

        if form.is_valid():
            print("Formulario válido")
            comision = form.save()

            # Actualizar categorías
            categorias = request.POST.getlist('categorias_seleccionadas')
            print("Categorías seleccionadas:", categorias)

            if len(categorias) > 3:
                return JsonResponse({
                    'success': False,
                    'error': 'Máximo 3 categorías por comisión.'
                }, status=400)

            comision.categorias = ','.join(categorias)
            comision.save()

            # Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'message': 'Comisión actualizada correctamente.',
                'comision': {
                    'id': comision.id,
                    'nombre': comision.nombre,
                    'precio': str(comision.precio),
                    'slots_disponibles': comision.slots_disponibles,
                    'tiempo_estimado': comision.tiempo_estimado,
                    'descripcion': comision.descripcion[:100],
                    'imagen_url': comision.imagen.url if comision.imagen else None,
                }
            })
        else:
            print("Errores del formulario:", form.errors)
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

class ComisionDeleteView(ArtistRequiredMixin, View):
    """Vista AJAX para eliminar comisión"""
    def post(self, request, *args, **kwargs):
        comision = get_object_or_404(Comision, id=kwargs['pk'])

        if comision.artista != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'No tienes permiso para eliminar esta comisión.'},
                                status=403)

        comision.delete()
        return JsonResponse({'success': True, 'message': 'Comisión eliminada correctamente.'})

    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


class ApiComisionesArtistaView(ArtistRequiredMixin, View):
    """Vista AJAX para obtener las comisiones del artista logueado"""

    def get(self, request, *args, **kwargs):
        if not request.user.es_artista():
            return JsonResponse({'comisiones': []})

        comisiones = Comision.objects.filter(artista=request.user).order_by('-creada_en')

        data = []
        for c in comisiones:
            data.append({
                'id': c.id,
                'nombre': c.nombre,
                'precio': str(c.precio),
                'slots_disponibles': c.slots_disponibles,
                'tiempo_estimado': c.tiempo_estimado,
                'descripcion': c.descripcion[:100],
                'imagen_url': c.imagen.url if c.imagen else None,
            })

        return JsonResponse({'comisiones': data})



# POLÍTICAS
class ApiPoliticasView(ArtistRequiredMixin, View):
    """Obtener todas las políticas del artista"""

    def get(self, request):
        politicas = Politica.objects.filter(artista=request.user).order_by('-creada_en')
        data = []
        for p in politicas:
            data.append({
                'id': p.id,
                'nombre': p.nombre,
                'info_general': p.info_general[:100],
            })
        return JsonResponse({'politicas': data})


class PoliticaDetailView(ArtistRequiredMixin, View):
    """Obtener datos de una política para editar"""

    def get(self, request, pk):
        politica = get_object_or_404(Politica, id=pk, artista=request.user)
        return JsonResponse({
            'success': True,
            'politica': {
                'id': politica.id,
                'nombre': politica.nombre,
                'info_general': politica.info_general,
                'metodos_pago': politica.metodos_pago,
                'revisiones': politica.revisiones,
                'tiempo_entrega': politica.tiempo_entrega,
                'uso': politica.uso,
                'derechos_propiedad': politica.derechos_propiedad,
                'reembolsos': politica.reembolsos,
                'comunicacion': politica.comunicacion,
            }
        })


class PoliticaCreateView(ArtistRequiredMixin, View):
    """Crear política con AJAX"""

    def post(self, request):
        form = PoliticaForm(request.POST)

        if form.is_valid():
            politica = form.save(commit=False)
            politica.artista = request.user
            politica.save()

            return JsonResponse({
                'success': True,
                'message': 'Política creada correctamente.',
                'politica': {
                    'id': politica.id,
                    'nombre': politica.nombre,
                    'info_general': politica.info_general[:100],
                }
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({'success': False, 'errors': errors}, status=400)


class PoliticaUpdateView(ArtistRequiredMixin, View):
    """Actualizar política con AJAX"""

    def post(self, request, pk):
        politica = get_object_or_404(Politica, id=pk, artista=request.user)
        form = PoliticaForm(request.POST, instance=politica)

        if form.is_valid():
            politica = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Política actualizada correctamente.',
                'politica': {
                    'id': politica.id,
                    'nombre': politica.nombre,
                    'info_general': politica.info_general[:100],
                }
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({'success': False, 'errors': errors}, status=400)


class PoliticaDeleteView(ArtistRequiredMixin, View):
    """Eliminar política con AJAX"""

    def post(self, request, pk):
        politica = get_object_or_404(Politica, id=pk, artista=request.user)
        politica.delete()
        return JsonResponse({'success': True, 'message': 'Política eliminada correctamente.'})


# PORTFOLIO
class PortfolioCreateView(ArtistRequiredMixin, View):
    """Subir imagen al portfolio con AJAX"""

    def post(self, request):
        titulo = request.POST.get('titulo', '')
        imagen = request.FILES.get('imagen')

        if not imagen:
            return JsonResponse({'success': False, 'error': 'Debes seleccionar una imagen.'}, status=400)

        # Crear la imagen en el portfolio
        portfolio_img = PortfolioImagen.objects.create(
            artista=request.user,
            imagen=imagen,
            titulo=titulo
        )

        return JsonResponse({
            'success': True,
            'message': 'Imagen subida correctamente.',
            'imagen': {
                'id': portfolio_img.id,
                'imagen_url': portfolio_img.imagen.url,
                'titulo': portfolio_img.titulo,
            }
        })


class PortfolioDetailView(ArtistRequiredMixin, View):
    """Obtener datos de una imagen del portfolio para editar"""

    def get(self, request, pk):
        imagen = get_object_or_404(PortfolioImagen, id=pk, artista=request.user)
        return JsonResponse({
            'success': True,
            'imagen': {
                'id': imagen.id,
                'imagen_url': imagen.imagen.url,
                'titulo': imagen.titulo,
            }
        })


class PortfolioDeleteView(ArtistRequiredMixin, View):
    """Eliminar imagen del portfolio con AJAX"""

    def post(self, request, pk):
        imagen = get_object_or_404(PortfolioImagen, id=pk, artista=request.user)
        imagen.delete()
        return JsonResponse({'success': True, 'message': 'Imagen eliminada correctamente.'})


class PortfolioUpdateView(ArtistRequiredMixin, View):
    """Actualizar imagen del portfolio (imagen y título)"""

    def post(self, request, pk):
        imagen = get_object_or_404(PortfolioImagen, id=pk, artista=request.user)
        titulo = request.POST.get('titulo', '')

        # Actualizar título
        imagen.titulo = titulo

        # Actualizar imagen si se subió una nueva
        if 'imagen' in request.FILES:
            imagen.imagen = request.FILES['imagen']

        imagen.save()

        return JsonResponse({
            'success': True,
            'message': 'Imagen actualizada correctamente.',
            'imagen': {
                'id': imagen.id,
                'imagen_url': imagen.imagen.url,
                'titulo': imagen.titulo,
            }
        })

class ApiPortfolioView(ArtistRequiredMixin, View):
    """Obtener todas las imágenes del portfolio del artista"""

    def get(self, request):
        imagenes = PortfolioImagen.objects.filter(artista=request.user).order_by('-fecha_subida')
        data = []
        for img in imagenes:
            data.append({
                'id': img.id,
                'imagen_url': img.imagen.url,
                'titulo': img.titulo,
            })
        return JsonResponse({'imagenes': data})

# SOLICITUDES DE ENCARGO
class SolicitudCreateView(ClientRequiredMixin, View):
    """Crear solicitud de encargo con AJAX"""

    def post(self, request, comision_id):
        comision = get_object_or_404(Comision, id=comision_id)

        # Verificar disponibilidad
        if not comision.esta_disponible:
            return JsonResponse({
                'success': False,
                'error': 'Esta comisión ya no tiene slots disponibles.'
            }, status=400)

        # Crear la solicitud
        solicitud = SolicitudEncargo.objects.create(
            cliente=request.user,
            comision=comision,
            email=request.POST.get('email'),
            instagram=request.POST.get('instagram', ''),
            descripcion_idea=request.POST.get('descripcion_idea'),
            referencias=request.FILES.get('referencias')
        )

        return JsonResponse({
            'success': True,
            'message': 'Solicitud enviada correctamente. El artista te responderá pronto.',
            'solicitud_id': solicitud.id
        })

    def get(self, request, comision_id):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


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


class ApiSolicitudesView(ArtistRequiredMixin, View):
    """Obtener todas las solicitudes del artista (para recargar sin recargar página)"""

    def get(self, request):
        solicitudes = SolicitudEncargo.objects.filter(
            comision__artista=request.user
        ).select_related('cliente', 'comision').order_by('-fecha_solicitud')

        data = []
        for s in solicitudes:
            data.append({
                'id': s.id,
                'cliente_username': s.cliente.username,
                'comision_nombre': s.comision.nombre,
                'descripcion': s.descripcion_idea[:100],
                'estado': s.estado,
                'estado_display': s.get_estado_display(),
                'fecha': s.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
            })
        return JsonResponse({'solicitudes': data})

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

#GUARDAR COMISIÓN
class GuardarComisionView(ClientRequiredMixin, View):
    """Vista para guardar o eliminar una comisión de favoritos (usando POST)"""

    def post(self, request, comision_id):
        comision = get_object_or_404(Comision, id=comision_id)
        guardado = ComisionGuardada.objects.filter(cliente=request.user, comision=comision)

        if guardado.exists():
            # Si ya está guardada, la eliminamos
            guardado.delete()
            messages.success(request, f"Comisión '{comision.nombre}' eliminada de favoritos.")
        else:
            # Si no está guardada, la añadimos
            ComisionGuardada.objects.create(cliente=request.user, comision=comision)
            messages.success(request, f"Comisión '{comision.nombre}' guardada en favoritos.")

        # Redirigir a la página anterior
        return redirect(request.META.get('HTTP_REFERER', 'home'))


#BÚSQUEDA
class BuscarComisionesView(ListView):
    model = Comision
    template_name = 'core/buscar_comisiones.html'
    context_object_name = 'comisiones'
    paginate_by = 12

    def get_queryset(self):
        queryset = Comision.objects.filter(activa=True)

        # Búsqueda por texto
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(artista__username__icontains=q)
            )

        # Filtro por categoría (usando el campo usos_permitidos como categoría)
        categoria = self.request.GET.get('categoria', '')
        if categoria:
            queryset = queryset.filter(categorias__icontains=categoria)

        # Filtro por precio
        precio_order = self.request.GET.get('precio', '')
        if precio_order == 'asc':
            queryset = queryset.order_by('precio')
        elif precio_order == 'desc':
            queryset = queryset.order_by('-precio')

        # Filtro por valoraciones (media de reseñas del artista)
        valoracion = self.request.GET.get('valoracion', '')
        if valoracion:
            queryset = queryset.annotate(
                media_artista=Avg('artista__reseñas_recibidas__puntuacion')
            ).filter(media_artista__gte=float(valoracion))

        return queryset.select_related('artista').prefetch_related('artista__perfil')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Comision.CATEGORIAS_CHOICES
        context['q'] = self.request.GET.get('q', '')
        context['categoria_seleccionada'] = self.request.GET.get('categoria', '')
        context['precio_seleccionado'] = self.request.GET.get('precio', '')
        context['valoracion_seleccionada'] = self.request.GET.get('valoracion', '')

        # Añadir el ID del usuario actual
        if self.request.user.is_authenticated:
            context['user_id'] = self.request.user.id
        else:
            context['user_id'] = 0

        return context

#MODAL DETALLE COMISIÓN
def comision_detalle_modal(request, comision_id):
    comision = get_object_or_404(Comision, id=comision_id, activa=True)
    user_id = request.user.id if request.user.is_authenticated else 0
    return render(request, 'core/comisiones/detalle_modal.html', {
        'comision': comision,
        'user_id': user_id
    })