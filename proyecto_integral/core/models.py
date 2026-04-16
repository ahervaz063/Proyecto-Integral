from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


# ============================================================
# USUARIO PERSONALIZADO
# ============================================================
class Usuario(AbstractUser):
    TIPO_USUARIO = (
        ('artista', 'Artista'),
        ('cliente', 'Cliente'),
        ('admin', 'Administrador'),
    )

    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO,
        default='cliente',
        verbose_name="Tipo de usuario"
    )
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de nacimiento")

    # Campos requeridos para crear superusuario
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_tipo_usuario_display()})"

    def es_artista(self):
        return self.tipo_usuario == 'artista'

    def es_cliente(self):
        return self.tipo_usuario == 'cliente'

    def es_admin(self):
        return self.is_staff or self.tipo_usuario == 'admin'



# PERFIL (OneToOne con Usuario)
class Perfil(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil',
        related_query_name='perfil'
    )
    foto = models.ImageField(
        upload_to='perfiles/',
        null=True,
        blank=True,
        verbose_name="Foto de perfil"
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción / Biografía")
    redes_sociales = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Redes sociales",
        help_text='Ej: {"instagram": "@usuario", "twitter": "@usuario", "behance": "url"}'
    )
    tarjeta = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Tarjeta (para pagos)",
        help_text="Solo para artistas"
    )

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    def save(self, *args, **kwargs):
        # Si es artista y no tiene tarjeta, mostrar advertencia (no bloqueante)
        if self.usuario.es_artista() and not self.tarjeta:
            pass  # Se puede añadir una señal o advertencia
        super().save(*args, **kwargs)



# POLÍTICA (solo artistas)
class Politica(models.Model):
    artista = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='politicas',
        related_query_name='politica',
        limit_choices_to={'tipo_usuario': 'artista'},
        verbose_name="Artista"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la política")

    # Campos del formulario de políticas
    info_general = models.TextField(verbose_name="Info general")
    metodos_pago = models.TextField(verbose_name="Métodos de pago")
    revisiones = models.TextField(verbose_name="Revisiones")
    tiempo_entrega = models.TextField(verbose_name="Tiempo de entrega")
    uso = models.TextField(verbose_name="Uso permitido")
    derechos_propiedad = models.TextField(verbose_name="Derechos de propiedad intelectual")
    reembolsos = models.TextField(verbose_name="Reembolsos")
    comunicacion = models.TextField(verbose_name="Comunicación")

    creada_en = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")
    actualizada_en = models.DateTimeField(auto_now=True, verbose_name="Actualizada el")

    class Meta:
        verbose_name = "Política"
        verbose_name_plural = "Políticas"
        ordering = ['-creada_en']
        unique_together = ['artista', 'nombre']  # Un artista no puede repetir nombre de política

    def __str__(self):
        return f"{self.nombre} - {self.artista.username}"



# COMISIÓN (solo artistas)
class Comision(models.Model):
    USOS_CHOICES = (
        ('personal', 'Uso personal'),
        ('comercial', 'Uso comercial'),
        ('monetizar', 'Monetizar contenido'),
        ('todos', 'Todos los usos'),
    )

    artista = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='comisiones',
        related_query_name='comision',
        limit_choices_to={'tipo_usuario': 'artista'},
        verbose_name="Artista"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la comisión")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (€)")
    slots = models.PositiveSmallIntegerField(default=1, verbose_name="Número de slots disponibles")
    slots_ocupados = models.PositiveSmallIntegerField(default=0, verbose_name="Slots ocupados")
    tiempo_estimado = models.PositiveSmallIntegerField(
        help_text="Días estimados para entregar",
        verbose_name="Tiempo estimado (días)"
    )
    descripcion = models.TextField(verbose_name="Descripción detallada")
    imagen = models.ImageField(
        upload_to='comisiones/',
        null=True,
        blank=True,
        verbose_name="Imagen de ejemplo"
    )
    politica = models.ForeignKey(
        Politica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comisiones',
        verbose_name="Política asociada"
    )
    usos_permitidos = models.CharField(
        max_length=20,
        choices=USOS_CHOICES,
        default='personal',
        verbose_name="Usos permitidos"
    )
    activa = models.BooleanField(default=True, verbose_name="Comisión activa")
    creada_en = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")
    actualizada_en = models.DateTimeField(auto_now=True, verbose_name="Actualizada el")

    class Meta:
        verbose_name = "Comisión"
        verbose_name_plural = "Comisiones"
        ordering = ['-creada_en']
        unique_together = ['artista', 'nombre']  # Un artista no puede repetir nombre de comisión

    def __str__(self):
        return f"{self.nombre} - {self.artista.username} (€{self.precio})"

    @property
    def slots_disponibles(self):
        """Devuelve los slots que aún están libres."""
        return self.slots - self.slots_ocupados

    @property
    def esta_disponible(self):
        """Indica si la comisión tiene al menos un slot disponible."""
        return self.slots_disponibles > 0 and self.activa

    def validar_slots(self):
        """Valida que los slots ocupados no superen los slots totales."""
        if self.slots_ocupados > self.slots:
            raise ValidationError("Los slots ocupados no pueden superar los slots totales.")

    def save(self, *args, **kwargs):
        self.validar_slots()
        super().save(*args, **kwargs)


# PORTFOLIO IMAGEN (solo artistas)
class PortfolioImagen(models.Model):
    artista = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='portfolio',
        related_query_name='portfolio',
        limit_choices_to={'tipo_usuario': 'artista'},
        verbose_name="Artista"
    )
    imagen = models.ImageField(upload_to='portfolio/', verbose_name="Imagen")
    titulo = models.CharField(max_length=200, blank=True, verbose_name="Título de la obra")
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name="Subida el")

    class Meta:
        verbose_name = "Imagen del portfolio"
        verbose_name_plural = "Imágenes del portfolio"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.titulo or 'Imagen'} - {self.artista.username}"

