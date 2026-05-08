# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Usuario, Perfil

@receiver(post_save, sender=Usuario)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea un perfil automáticamente cuando se crea un nuevo usuario"""
    if created:
        Perfil.objects.get_or_create(usuario=instance)
        print(f"Perfil creado para {instance.username}")

@receiver(post_save, sender=Usuario)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    if hasattr(instance, 'perfil') and instance.perfil:
        instance.perfil.save()