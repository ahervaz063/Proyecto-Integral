# core/urls.py
from django.urls import path
from core import views

urlpatterns = [
    # Públicas
    path('', views.HomeView.as_view(), name='home'),
    path('buscar/', views.BuscarArtistasView.as_view(), name='buscar'),

    # Autenticación
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Perfiles
    path('artista/<int:pk>/', views.PerfilArtistaView.as_view(), name='perfil_artista'),
    path('cliente/<int:pk>/', views.PerfilClienteView.as_view(), name='perfil_cliente'),
    path('editar-perfil/', views.EditarPerfilView.as_view(), name='editar_perfil'),

    # Comisiones
    path('comisiones/<int:pk>/', views.ComisionDetailView.as_view(), name='comision_detail'),
    path('comisiones/crear/', views.ComisionCreateView.as_view(), name='comision_create'),
    path('comisiones/<int:pk>/editar/', views.ComisionUpdateView.as_view(), name='comision_update'),
    path('comisiones/<int:pk>/eliminar/', views.ComisionDeleteView.as_view(), name='comision_delete'),
    path('comision/<int:comision_id>/guardar/', views.GuardarComisionView.as_view(), name='guardar_comision'),

    #Comisiones AJAX
    path('api/comisiones/', views.ApiComisionesArtistaView.as_view(), name='api_comisiones'),
    path('comisiones/<int:pk>/datos/', views.ComisionDetailView.as_view(), name='comision_datos'),
    path('comisiones/crear/', views.ComisionCreateView.as_view(), name='comision_create'),
    path('comisiones/<int:pk>/editar/', views.ComisionUpdateView.as_view(), name='comision_update'),
    path('comisiones/<int:pk>/eliminar/', views.ComisionDeleteView.as_view(), name='comision_delete'),

    # Políticas
    path('api/politicas/', views.ApiPoliticasView.as_view(), name='api_politicas'),
    path('politicas/crear/', views.PoliticaCreateView.as_view(), name='politica_create'),
    path('politicas/<int:pk>/datos/', views.PoliticaDetailView.as_view(), name='politica_datos'),
    path('politicas/<int:pk>/editar/', views.PoliticaUpdateView.as_view(), name='politica_update'),
    path('politicas/<int:pk>/eliminar/', views.PoliticaDeleteView.as_view(), name='politica_delete'),

    # Portfolio
    path('api/portfolio/', views.ApiPortfolioView.as_view(), name='api_portfolio'),
    path('portfolio/subir/', views.PortfolioCreateView.as_view(), name='portfolio_create'),
    path('portfolio/<int:pk>/eliminar/', views.PortfolioDeleteView.as_view(), name='portfolio_delete'),
    path('portfolio/<int:pk>/datos/', views.PortfolioDetailView.as_view(), name='portfolio_datos'),
    path('portfolio/<int:pk>/editar/', views.PortfolioUpdateView.as_view(), name='portfolio_update'),

    # Solicitudes
    path('solicitud/crear/<int:comision_id>/', views.SolicitudCreateView.as_view(), name='solicitud_create'),
    path('solicitudes/artista/', views.SolicitudesArtistaListView.as_view(), name='solicitudes_artista'),
    path('solicitudes/cliente/', views.SolicitudesClienteListView.as_view(), name='mis_solicitudes_cliente'),
    path('solicitud/<int:solicitud_id>/aceptar/', views.aceptar_solicitud, name='aceptar_solicitud'),
    path('solicitud/<int:solicitud_id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('solicitud/<int:solicitud_id>/cancelar/', views.cancelar_solicitud, name='cancelar_solicitud'),
    path('solicitud/<int:solicitud_id>/finalizar/', views.finalizar_encargo, name='finalizar_encargo'),
    path('api/solicitudes/', views.ApiSolicitudesView.as_view(), name='api_solicitudes'),

    # Reseñas
    path('resena/crear/<int:solicitud_id>/', views.ResenaCreateView.as_view(), name='resena_create'),

    #Búsqueda
    path('buscar/comisiones/', views.BuscarComisionesView.as_view(), name='buscar_comisiones'),
    path('comision/<int:comision_id>/detalle-modal/', views.comision_detalle_modal, name='comision_detalle_modal'),
]